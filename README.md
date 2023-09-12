# ueGear
Unreal Engine Gear


### ueGear 1.0 Roadmap Goals
**Goal:** 

  - Generate a simple Runtime rig with Control Rig
  - Generate Full Animation rig with Control Rig
  - Generate IKRig with retargeting mapping
  - IO layout data (Cameras + static Mesh + skeletal mesh)
  - Assembly of modular characters

**New tools:**
  - Core libraries
  - Control rig function solvers like Maya counterpart 
  - ueShifter:
    - EPIC component counterpart to build from Collected data in Maya

### mGear 4.3 counterpart/Pipeline tools for ueGear
These tools will be implemented in mGear

**Goal:**

 - improve game pipeline
 - gNexus (.gnx): General data collector for ueGear 

**New tools:**

  - FBX exporter  
      - 1click send to Unreal (FBX) Skeletal mesh and animation



# Unreal Plugins
The following plugins must be activated in your project to get the full benefit of ueGear.
- `Python Editor Script Plugin`
- `Sequencer Scripting`
- `Remote Control API`, Required for Maya to pipe queries into Unreal

# Workflow

## New Maya Scene, Existing Level and Sequencer Data
1. Open `Maya` and `Unreal`
2. Make sure that mGear is installed for both applications.
3. In `Unreal`, Open the `Level` and LevelSeqence in `Sequencer`, that you want to work on.

**NOTE**: Any information that is in the Sequencer and outside of the `Playback` region (red/green lines), will not be exported. This means animation keys on the camera. 
[Functionality could be added at a later date to implement entire camera track sections get exported even if outside of the Playback region]
