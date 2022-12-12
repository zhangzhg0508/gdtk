// transient_calc.d -- Part of the Lorikeet transient-flow calculator.
//
// PA Jacobs
// 2022-12-12: Adapt from Puffin and Chicken codes.
//
module transient_calc;

import std.conv;
import std.stdio;
import std.string;
import std.json;
import std.file;
import std.datetime;
import std.format;
import std.range;
import std.math;
import std.algorithm;

import json_helper;
import geom;
import config;
import fluidblock;

// We use __gshared so that several threads may access
// the following array concurrently.
__gshared static FluidBlock[] fluidBlocks;

struct ProgressData {
    int step = 0; // steps so far
    double t = 0.0; // time at start of gas-dynamic update
    double dt = 0.0; // increment of time for the gas-dynamic update
    int tindx = 0; // index of the flow data just read or written
    double plot_at_t = 0.0; // time at which to write another blob of flow data
    double[] dt_values; // a place to store the allowable dt for each block
    int steps_since_last_plot_write = 0;
    SysTime wall_clock_start;
}

__gshared static ProgressData progress;

void init_simulation(int tindx)
// Set up configuration and read block data for a given tindx.
{
    string dirName = Config.job_name;
    JSONValue configData = readJSONfile(dirName~"/config.json");
    Config.title = getJSONstring(configData, "title", "");
    Config.gas_model_file = getJSONstring(configData, "gas_model_file", "");
    Config.reaction_file_1 = getJSONstring(configData, "reaction_files_1", "");
    Config.reaction_file_2 = getJSONstring(configData, "reaction_file_2", "");
    Config.reacting = getJSONbool(configData, "reacting", false);
    Config.T_frozen = getJSONdouble(configData, "T_frozen", 300.0);
    Config.axisymmetric = getJSONbool(configData, "axisymmetric", false);
    Config.max_t = getJSONdouble(configData, "max_t", 0.0);
    Config.max_step = getJSONint(configData, "max_step", 0);
    Config.dt_init = getJSONdouble(configData, "dt_init", 1.0e-6);
    Config.cfl = getJSONdouble(configData, "cfl", 0.5);
    Config.print_count = getJSONint(configData, "print_count", 50);
    Config.plot_dx = getJSONdouble(configData, "plot_dx", 1.0e-2);
    Config.x_order = getJSONint(configData, "x_order", 2);
    Config.t_order = getJSONint(configData, "t_order", 2);
    Config.flux_calc = to!FluxCalcCode(getJSONint(configData, "flux_calc", 0));
    Config.compression_tol = getJSONdouble(configData, "compression_tol", -0.3);
    Config.shear_tol = getJSONdouble(configData, "shear_tol", 0.2);
    Config.n_blocks = getJSONint(configData, "n_blocks", 1);
    if (Config.verbosity_level >= 1) {
        writeln("Config:");
        writefln("  title= \"%s\"", Config.title);
        writeln("  gas_model_files= ", Config.gas_model_file);
        writeln("  reaction_files_1= ", Config.reaction_file_1);
        writeln("  reaction_files_2= ", Config.reaction_file_2);
        writeln("  reacting= ", Config.reacting);
        writeln("  T_frozen= ", Config.T_frozen);
        writeln("  axisymmetric= ", Config.axisymmetric);
        writeln("  max_t= ", Config.max_t);
        writeln("  max_step= ", Config.max_step);
        writeln("  dt_init= ", Config.dt_init);
        writeln("  max_step_relax= ", Config.max_step_relax);
        writeln("  cfl= ", Config.cfl);
        writeln("  print_count= ", Config.print_count);
        writeln("  plot_dt= ", Config.plot_dt);
        writeln("  x_order= ", Config.x_order);
        writeln("  t_order= ", Config.t_order);
        writeln("  flux_calc= ", Config.flux_calc);
        writeln("  compression_tol= ", Config.compression_tol);
        writeln("  shear_tol= ", Config.shear_tol);
        writeln("  n_blocks= ", Config.n_blocks);
    }
    foreach (i; 0 .. Config.n_blocks) {
        fluidBlocks ~= new FluidBlock(i, configData);
        if (Config.verbosity_level >= 1) {
            writefln("  fluidBlocks[%d]= %s", i, fluidBlocks[i]);
        }
    }
    //
    foreach (b; fluidBlocks) {
        b.set_up_data_storage();
        b.read_grid_data();
        b.set_up_geometry();
        b.read_flow_data(tindx);
    }
    progress.step = 0;
    progress.t = 0.0;
    progress.dt = Config.dt_init;
    progress.tindx = tindx;
    progress.plot_at_t = Config.plot_dt;
    progress.steps_since_last_plot_write = 0;
    progress.dt_values.length = fluidBlocks.length;
    return;
} // end init_calculation()


void do_time_integration()
{
    progress.wall_clock_start = Clock.currTime();
    foreach (b; fluidBlocks) {
        b.encode_conserved(0);
    }
    while (progress.t < Config.max_t || progress.step < Config.max_step) {
        // 1. Occasionally set size of time step.
        if (progress.step > 0 && (progress.step % Config.cfl_count)==0) {
            foreach (j, b; fluidBlocks) { // FIXME can do in parallel
                progress.dt_values[j] = b.estimate_allowable_dt();
            }
            double smallest_dt = progress.dt_values[0];
            foreach (j; 1 .. progress.dt_values.length) {
                smallest_dt = fmin(smallest_dt, progress.dt_values[j]);
            }
            // Make the transition to larger allowable time step not so sudden.
            progress.dt = fmin(1.5*progress.dt, smallest_dt);
        }
        // 2. Take a step.
        int attempt_number = 0;
        bool step_failed;
        do {
            ++attempt_number;
            step_failed = false;
            try {
                gas_dynamic_update(progress.dt);
            } catch (Exception e) {
                writefln("Step failed e.msg=%s", e.msg);
                step_failed = true;
                progress.dt *= 0.2;
            }
        } while (step_failed && (attempt_number <= 3));
        if (step_failed) {
            throw new Exception("Step failed after 3 attempts.");
        }
        //
        // 3. Prepare for next time step.
        foreach (b; fluidBlocks) { b.transfer_conserved_quantities(2, 0); }
        progress.t += progress.dt;
        progress.step++;
        //
        // 4. Occasional console output.
        if (Config.verbosity_level >= 1 &&
            ((progress.step % Config.print_count) == 0)) {
            // For reporting wall-clock time, convert with precision of milliseconds.
            auto elapsed_ms = (Clock.currTime() - progress.wall_clock_start).total!"msecs"();
            double elapsed_s = to!double(elapsed_ms)/1000;
            double WCtFT = ((progress.t > 0.0) && (progress.step > 0)) ?
                elapsed_s*(Config.max_t-progress.t)/progress.dt/progress.step : 0.0;
            writefln("Step=%d t=%.3e dt=%.3e WC=%.1f WCtFT=%.1f",
                     progress.step, progress.t, progress.dt, elapsed_s, WCtFT);
            stdout.flush();
        }
        //
        // 5. Write a flow solution (maybe).
        if (progress.t >= progress.plot_at_t) {
            int tindx = progress.tindx + 1;
            foreach (b; fluidBlocks) { b.write_flow_data(tindx); }
            // FIXME append to times file.
            progress.steps_since_last_plot_write = 0;
            progress.plot_at_t += Config.plot_dt;
            progress.tindx = tindx;
        } else {
            progress.steps_since_last_plot_write++;
        }
    } // end while
    //
    // Write the final slice, maybe.
    if (progress.steps_since_last_plot_write > 0) {
        int tindx = progress.tindx + 1;
        foreach (b; fluidBlocks) { b.write_flow_data(tindx); }
        // FIXME append to times file.
        progress.tindx = tindx;
    }
    return;
} // end do_time integration()


@nogc
void gas_dynamic_update(double dt)
// Work across all blocks, attempting to integrate the conserved quantities
// over an increment of time, dt.
{
    //
    foreach (k; 0 .. Config.max_step_relax) {
        // 1. Predictor (Euler) step..
        apply_boundary_conditions();
        foreach (b; fluidBlocks) { b.mark_shock_cells(); }
        foreach (b; fluidBlocks) { b.predictor_step(dt); }
        if (Config.t_order > 1) {
            apply_boundary_conditions();
            foreach (b; fluidBlocks) {
                b.corrector_step(dt);
                b.transfer_conserved_quantities(2, 0);
            }
        } else {
            // Clean-up after Euler step.
            foreach (b; fluidBlocks) {
                b.transfer_conserved_quantities(1, 0);
            }
        }
    }
    return;
} // end gas_dynamic_update()

@nogc
void apply_boundary_conditions()
// Application of the boundary conditions is essentially filling the
// ghost-cell flow states with suitable data.
{
    foreach (b; fluidBlocks) {
        /+
        int bc0 = st.bc_lower.get_value(xmid);
        switch (bc0) {
        case BCCode.wall:
            // The slip-wall condition is implemented by filling the ghost cells
            // with reflected-normal-velocity flow.
            auto fstate = &(st.ghost_cells_left[0].fs);
            auto face = st.jfaces[0];
            fstate.copy_values_from(st.cells[0].fs);
            fstate.vel.transform_to_local_frame(face.n, face.t1);
            fstate.vel.x = -(fstate.vel.x);
            fstate.vel.transform_to_global_frame(face.n, face.t1);
            //
            fstate = &(st.ghost_cells_left[1].fs);
            fstate.copy_values_from(st.cells[1].fs);
            fstate.vel.transform_to_local_frame(face.n, face.t1);
            fstate.vel.x = -(fstate.vel.x);
            fstate.vel.transform_to_global_frame(face.n, face.t1);
            break;
        case BCCode.exchange:
            // We fill the ghost-cells with data drom the neighbour streamtube.
            auto nst = streams[i-1];
            st.ghost_cells_left[0].fs.copy_values_from(nst.cells[nst.ncells-1].fs);
            st.ghost_cells_left[1].fs.copy_values_from(nst.cells[nst.ncells-2].fs);
            break;
        default:
            throw new Exception("Unknown BCCode.");
        }
        int bc1 = st.bc_upper.get_value(xmid);
        switch (bc1) {
        case BCCode.wall:
            auto fstate = &(st.ghost_cells_right[0].fs);
            auto face = st.jfaces[st.ncells];
            fstate.copy_values_from(st.cells[st.ncells-1].fs);
            fstate.vel.transform_to_local_frame(face.n, face.t1);
            fstate.vel.x = -(fstate.vel.x);
            fstate.vel.transform_to_global_frame(face.n, face.t1);
            //
            fstate = &(st.ghost_cells_right[1].fs);
            fstate.copy_values_from(st.cells[st.ncells-2].fs);
            fstate.vel.transform_to_local_frame(face.n, face.t1);
            fstate.vel.x = -(fstate.vel.x);
            fstate.vel.transform_to_global_frame(face.n, face.t1);
            break;
        case BCCode.exchange:
            // We fill the ghost-cells with data drom the neighbour streamtube.
            auto nst = streams[i+1];
            st.ghost_cells_right[0].fs.copy_values_from(nst.cells[0].fs);
            st.ghost_cells_right[1].fs.copy_values_from(nst.cells[1].fs);
            break;
        default:
            throw new Exception("Unknown BCCode.");
        }
+/
    } // end foreach b
    return;
} // end apply_boundary_conditions()