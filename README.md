# ueGear
Unreal Engine Gear

Requires: Unreal 5.2+

### ueGear 0.1 Roadmap Goals
**Goal:** 
  - IO layout data (Cameras + static Mesh + skeletal mesh)

**New tools:**
  - Core libraries

#### mGear 4.3 counterpart/Pipeline tools for ueGear
These tools will be implemented in mGear

**Goal:**
 - improve game pipeline


### ueGear 0.2 Roadmap Goals
**Goal:** 
  - Syncing selected assets in Unreal Levels with Maya.
  

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

#### mGear 4.3 counterpart/Pipeline tools for ueGear
These tools will be implemented in mGear

**Goal:**

 - improve game pipeline
 - gNexus (.gnx): General data collector for ueGear 

**New tools:**

  - FBX exporter  
      - 1click send to Unreal (FBX) Skeletal mesh and animation

# DESIGN DECISIONS
- Always starting from Unreal
- Always assume camera in sequencer
Unreal > Maya > Unreal camera flows
- Adding custom attributes on Camera to FBX
- A shot represents one Camera track.


# Unreal Plugins
The following plugins must be activated in your project to get the full benefit of ueGear.
- `Python Editor Script Plugin`
- `Sequencer Scripting`
- `Remote Control API`, Required for Maya to pipe queries into Unreal

# Workflow

## New Maya Scene, Existing Level and Sequencer Data
**NOTE**: Before starting you will need to have `MGEAR_FBX_SDK_PATH` setup in your environment varialbes, and have it pointing to an FBX SDK, which can be downloaded from [SDK](https://www.autodesk.com/developer-network/platform-technologies/fbx-sdk-2020-0)

**WIP: Working on making the Maya to Unreal workflow not require FBX SDK, as this adds a level of complexity for the User.**

1. Open `Maya` and `Unreal`
2. Make sure that mGear is installed for both applications (mGear, ueGear).
3. In `Unreal`, Open the `Level` and LevelSeqence in `Sequencer`, that you want to work on.

**NOTE**: Any information that is in the Sequencer and outside of the `Playback` region (red/green lines), will not be exported. This means animation keys on the camera. 
[Functionality could be added at a later date to implement entire camera track sections get exported even if outside of the Playback region]

# FBX SDK Setup

## OSX
Go to the FBX webpage and install the latest version that works with your Maya version.

# Unreal Cameras
- Can exist in LevelSequencer
- Can exist in a sub sequence of a LevelSequencer
- Can be instantiated by the LevelSequencer
- Can exist in a Level and not in a LevelSequencer
- Never exists in the Content Browser. It will appear in a LevelSequence or inside a level.

# Control Rig

The ueGear Control Rig Library can be found in the following location
Repo: `ueGear/Plugins/ueGear/Content/Python/ueGear/controlrig/ueGearFunctionLibrary.uasset`
Unreal: `ueGear/Content/Python/ueGear/controlrig/ueGearFunctionLibrary.uasset`

If you enable plugins in the Content Browser Settings, you will be able to see the folder.
