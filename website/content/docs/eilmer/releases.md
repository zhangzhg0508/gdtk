---
title: "Releases"
description: "Eilmer Releases"
lead: ""
date: 2021-07-28
lastmod: 2020-07-28
draft: false
images: []
menu:
  docs:
    parent: "eilmer"
weight: 15
toc: true
---

The Eilmer project is active and the code is under constant development.
You can follow this cutting edge development work by checking out
the master branch of the repository, and performing frequent updates with git pull.
We try to ensure that the latest revisions are ready for general use.
We recommend this mode of code updates for advanced users or those
interested in the advanced new feature sets.
This type of release mode is known as a rolling release, and we offer
this as one way of using the toolkit.

We also offer numbered "release versions".
These are snapshots of the code's history that do not get altered over time.
Each release comes with a list of officially supported features;
those are shown on this webpage.
Each feature in the list is an item that we consider to be well tested
and has good supporting documentation.
These are features we are happy to support in the long term.
If you only require the capabilities on the supported list,
you should consider using a numbered release version.


## Why do we have this two-mode release model?

Eilmer has a large collection of features, because, well, hypersonic flows have a large
range of pertinent physics to model.
Some features are bleeding-edge, some features are experimental, some features lack documentation,
and some features are still buggy.
This acknowledges that new model development needs time to mature and undergo real-world testing.
On the other hand, we have pieces of the code that have been battle-hardened over 30 years.
This leads to a spectrum of feature-readiness that covers a wide range of usability,
with some features being extremely experimental (read: unstable) and others as reliable
as they practicably could be.

We need to convey this information about feature readiness to our users.
We have decided to use numbered releases as that mechanism to convey the maturity
of the releases.
In particular, the list of features that accompanies each release are the officially
supported features.
You can expect these features to work and expect prompt bug fixes if any issues aries.
The other features of the code are still available for use, but should be considered
experimental.
These come with a *caveat emptor*: bug fixes are lower priority in our development
schedule and documentation may not be complete as the feature development is evolving.

This page will document the set of features officially supported in each release.

## Version 4.0.0

**Release date: 2021-07-29**

If you **do not** already have a copy of the repository, first clone it:

    git clone https://bitbucket.org/cfcfd/dgd-git dgd

If you **do** have a copy of the repository, get it up to date:

    cd dgd
    git pull 

From **within** the `dgd` directory, checkout this verstion:

    git checkout v4.0.0


Capabilities/features supported in `v4.0.0`.

+ transient time-stepping
  + Euler
  + predictor-corrector
  + RK-3 variants
+ local time-stepping
+ grid capabilities
  + structured grids
  + unstructured grids
  + moving grid (user-defined motion and shock-fitting)
  + import GridPro format
  + import SU2 format
+ parallel execution
  + with shared memory (on NUMA platforms)
  + with MPI (for inter- and intra-node execution)
+ gas models
  + ideal gas
  + mixtures of thermally perfect gases
+ kinetics
  + finite-rate chemistry (for thermally perfect gas mixtures)
+ turbulence models
  + Spalart-Allmaras
  + k-$\omega$
+ conjugate heat transfer (coupling fluid/solid domains)
  + structured grids in 2D or 3D
+ shock-fitting
+ user-defined run-time customisation for:
  + initial conditions
  + boundary conditions	
  + source terms
  + grid motion
+ block-marching mode






