#! /usr/bin/env python3
"""
Python program to post-process the simulation data from the Chicken 3D Flow Solver.

Usage:
  $ chkn-post --job=<jobName>

Author:
  P.A. Jacobs

Versions:
  2022-09-23  First Python code adpated from chkn_prep.py
"""

# ----------------------------------------------------------------------
#
import sys
import os
from getopt import getopt
import math
from copy import copy
import numpy as np
import json
from zipfile import ZipFile

from gdtk.geom.vector3 import Vector3, hexahedron_properties
from gdtk.geom.sgrid import StructuredGrid


shortOptions = "hft:"
longOptions = ["help", "job=", "tindx="]

def printUsage():
    print("Post-process a chicken run to produce VTK format files.")
    print("Usage: chkn-post" +
          " [--help | -h]" +
          " [--job=<jobName> | -f <jobName>]" +
          " [--tindx=<int> | -t <int>"
    )
    print("")
    return

# --------------------------------------------------------------------

config = {}
times = {}
grids = {}
flows = {}

def read_config(jobDir):
    """
    Read the config and times files.
    """
    global config, times
    text = open(jobDir + '/config.json', 'r').read()
    config = json.loads(text)
    text = open(jobDir + '/times.data', 'r').readlines()
    for line in text:
        if len(line.strip()) == 0: continue
        if line[0] == '#': continue
        items = line.strip().split()
        times[int(items[0])] = float(items[1])
    return

def read_grids(jobDir):
    """
    Read the full set of grids.
    """
    global config
    gridDir = jobDir+'/grid'
    if not os.path.exists(gridDir):
        raise RuntimeError('Cannot find grid directory: ' + gridDir)
    for k in range(config['nkb']):
        for j in range(config['njb']):
            for i in range(config['nib']):
                fileName = gridDir + ('/grid-%04d-%04d-%04d.gz' % (i, j, k))
                if os.path.exists(fileName):
                    grids['%d,%d,%d'%(i,j,k)] = StructuredGrid(gzfile=fileName)
    return

def read_flow_blocks(jobDir, tindx):
    """
    Read the flow blocks for an individual tindx.
    """
    global config
    flowDir = jobDir + ('/flow/t%04d' % tindx)
    if not os.path.exists(flowDir):
        raise RuntimeError('Cannot find flow directory: ' + flowDir)
    for k in range(config['nkb']):
        for j in range(config['njb']):
            for i in range(config['nib']):
                fileName = flowDir + ('/flow-%04d-%04d-%04d.zip' % (i, j, k))
                if os.path.exists(fileName):
                    flows['%d,%d,%d'%(i,j,k)] = read_block_of_flow_data(fileName)
    return

def read_block_of_flow_data(fileName):
    """
    Unpack a zip archive to get the flow field data as lists of float numbers.
    """
    global config
    flowData = {}
    with ZipFile(fileName, mode='r') as zf:
        for var in config["flow_var_names"]:
            with zf.open(var, mode='r') as fp:
                text = fp.read().decode('utf-8')
                data = []
                for item in text.split('\n'):
                    if len(item) > 0: data.append(float(item))
                flowData[var] = data
    return flowData

# --------------------------------------------------------------------

def write_vtk_files(jobDir, tindx):
    """
    Write the collection of VTK files for a single tindx.
    """
    global config, grids, flows
    plotDir = jobDir + '/plot'
    if not os.path.exists(plotDir): os.mkdir(plotDir)
    whole_niv = sum(config['nics']) + 1
    whole_njv = sum(config['njcs']) + 1
    whole_nkv = sum(config['nkcs']) + 1
    # The coordinating .pvts file is written as we write the individual .vts files.
    fileName = plotDir + ('/flow-t%04d.pvts' % (tindx,))
    fp = open(fileName, mode='w')
    fp.write('<VTKFile type="PStructuredGrid" version="0.1" byte_order="BigEndian">\n')
    fp.write('<PStructuredGrid WholeExtent="%d %d %d %d %d %d" GhostLevel="0">\n' %
             (0, whole_niv-1, 0, whole_njv-1, 0, whole_nkv-1))
    fp.write('<PCellData>\n')
    for var in config["flow_var_names"]:
        fp.write('<DataArray Name="%s" type="Float64" NumberOfComponents="1" format="ascii" />\n' % (var,))
    fp.write('</PCellData>\n')
    fp.write('<PPoints>\n')
    fp.write('<DataArray type="Float64" NumberOfComponents="3" format="ascii" />\n')
    fp.write('</PPoints>\n')
    start_nkv = 0
    for k in range(config['nkb']):
        start_njv = 0
        for j in range(config['njb']):
            start_niv = 0
            for i in range(config['nib']):
                fileName = 'flow-t%04d-%04d-%04d-%04d.vts' % (tindx, i, j, k)
                key = '%d,%d,%d'%(i,j,k)
                grid = grids[key]
                fp.write('<Piece Extent="%d %d %d %d %d %d" Source="%s" />\n' %
                         (start_niv, start_niv+grid.niv-1,
                          start_njv, start_njv+grid.njv-1,
                          start_nkv, start_nkv+grid.nkv-1, fileName))
                write_vtk_structured_grid_file(plotDir+'/'+fileName, grid, flows[key],
                                               whole_niv, whole_njv, whole_nkv,
                                               start_niv, start_njv, start_nkv)
                start_niv += config['nics'][i]
            start_njv += config['njcs'][j]
        start_nkv += config['nkcs'][k]
    fp.write('</PStructuredGrid>\n')
    fp.write('</VTKFile>\n')
    fp.close()
    return

def write_vtk_structured_grid_file(fileName, grid, flowData,
                                   whole_niv, whole_njv, whole_nkv,
                                   start_niv, start_njv, start_nkv):
    """
    Combine the grid and flow data for one block into a VTK StructuredGrid file.
    """
    with open(fileName, mode='w') as fp:
        fp.write('<VTKFile type="StructuredGrid" version="0.1" byte_order="BigEndian">\n')
        fp.write('<StructuredGrid WholeExtent="%d %d %d %d %d %d">\n' %
                 (0, whole_niv-1, 0, whole_njv-1, 0, whole_nkv-1))
        fp.write('<Piece Extent="%d %d %d %d %d %d">\n' %
                 (start_niv, start_niv+grid.niv-1,
                  start_njv, start_njv+grid.njv-1,
                  start_nkv, start_nkv+grid.nkv-1))
        fp.write('<CellData>\n')
        for var in config["flow_var_names"]:
            fp.write('<DataArray Name="%s" type="Float64" NumberOfComponents="1" format="ascii">\n' % (var,))
            for item in flowData[var]: fp.write('%g\n' % (item,))
            fp.write('</DataArray>\n')
        fp.write('</CellData>\n')
        fp.write('<Points>\n')
        fp.write('<DataArray type="Float64" NumberOfComponents="3" format="ascii">\n')
        for k in range(grid.nkv):
            for j in range(grid.njv):
                for i in range(grid.niv):
                    vtx = grid.vertices[i][j][k]
                    fp.write('%g %g %g\n'%(vtx.x, vtx.y, vtx.z))
        fp.write('</DataArray>\n')
        fp.write('</Points>\n')
        fp.write('</Piece>\n')
        fp.write('</StructuredGrid>\n')
        fp.write('</VTKFile>\n')
    return

# --------------------------------------------------------------------

if __name__ == '__main__':
    print("Begin chkn-post...")

    userOptions = getopt(sys.argv[1:], shortOptions, longOptions)
    uoDict = dict(userOptions[0])
    if len(userOptions[0]) == 0 or \
           "--help" in uoDict or \
           "-h" in uoDict:
        printUsage()
    else:
        if "--job" in uoDict:
            jobName = uoDict.get("--job", "")
        elif "-f" in uoDict:
            jobName = uoDict.get("-f", "")
        else:
            raise Exception("Job name is not specified.")
        jobDir, ext = os.path.splitext(jobName)
        #
        read_config(jobDir)
        print("times=", times)
        print("config=", config)
        read_grids(jobDir)
        # print('grids=', grids)
        #
        tindx = 0 # default is the initial-time index
        if "--tindx" in uoDict:
            tindx = int(uoDict.get("--tindx", "0"))
        elif "-t" in uoDict:
            tindx = int(uoDict.get("-t", "0"))
        read_flow_blocks(jobDir, tindx)
        # print('flows=', flows)
        write_vtk_files(jobDir, tindx)
        #
        print("Done.")
    #
    sys.exit(0)