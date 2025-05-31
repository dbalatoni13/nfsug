#!/usr/bin/env python3

###
# Generates build files for the project.
# This file also includes the project configuration,
# such as compiler flags and the object matching status.
#
# Usage:
#   python3 configure.py
#   ninja
#
# Append --help to see available options.
###

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List

from tools.project import (
    Object,
    ProgressCategory,
    ProjectConfig,
    calculate_progress,
    generate_build,
    is_windows,
)

# Game versions
DEFAULT_VERSION = 0
VERSIONS = [
    "GNDP8P",  # 0
]

parser = argparse.ArgumentParser()
parser.add_argument(
    "mode",
    choices=["configure", "progress"],
    default="configure",
    help="script mode (default: configure)",
    nargs="?",
)
parser.add_argument(
    "-v",
    "--version",
    choices=VERSIONS,
    type=str.upper,
    default=VERSIONS[DEFAULT_VERSION],
    help="version to build",
)
parser.add_argument(
    "--build-dir",
    metavar="DIR",
    type=Path,
    default=Path("build"),
    help="base build directory (default: build)",
)
parser.add_argument(
    "--binutils",
    metavar="BINARY",
    type=Path,
    help="path to binutils (optional)",
)
parser.add_argument(
    "--compilers",
    metavar="DIR",
    type=Path,
    help="path to compilers (optional)",
)
parser.add_argument(
    "--map",
    action="store_true",
    help="generate map file(s)",
)
parser.add_argument(
    "--debug",
    action="store_true",
    help="build with debug info (non-matching)",
)
if not is_windows():
    parser.add_argument(
        "--wrapper",
        metavar="BINARY",
        type=Path,
        help="path to wibo or wine (optional)",
    )
parser.add_argument(
    "--dtk",
    metavar="BINARY | DIR",
    type=Path,
    help="path to decomp-toolkit binary or source (optional)",
)
parser.add_argument(
    "--objdiff",
    metavar="BINARY | DIR",
    type=Path,
    help="path to objdiff-cli binary or source (optional)",
)
parser.add_argument(
    "--sjiswrap",
    metavar="EXE",
    type=Path,
    help="path to sjiswrap.exe (optional)",
)
parser.add_argument(
    "--verbose",
    action="store_true",
    help="print verbose output",
)
parser.add_argument(
    "--non-matching",
    dest="non_matching",
    action="store_true",
    help="builds equivalent (but non-matching) or modded objects",
)
parser.add_argument(
    "--no-progress",
    dest="progress",
    action="store_false",
    help="disable progress calculation",
)
args = parser.parse_args()

config = ProjectConfig()
config.version = str(args.version)
version_num = VERSIONS.index(config.version)

# Apply arguments
config.build_dir = args.build_dir
config.dtk_path = args.dtk
config.objdiff_path = args.objdiff
config.binutils_path = args.binutils
config.compilers_path = args.compilers
config.generate_map = args.map
config.non_matching = args.non_matching
config.sjiswrap_path = args.sjiswrap
config.progress = args.progress
if not is_windows():
    config.wrapper = args.wrapper
# Don't build asm unless we're --non-matching
if not config.non_matching:
    config.asm_dir = None

# Tool versions
config.binutils_tag = "2.42-1"
config.compilers_tag = "20250513"
config.dtk_tag = "v1.5.2"
config.objdiff_tag = "v2.7.1"
config.sjiswrap_tag = "v1.2.0"
config.wibo_tag = "0.6.11"

# Project
config.config_path = Path("config") / config.version / "config.yml"
config.check_sha_path = Path("config") / config.version / "build.sha1"
config.asflags = [
    "-mgekko",
    "--strip-local-absolute",
    "-I include",
    f"-I build/{config.version}/include",
    f"--defsym BUILD_VERSION={version_num}",
]
ldscript_path = Path("config") / config.version / "ldscript.ld"
config.ldflags = ["-T", str(ldscript_path)]

# Use for any additional files that should cause a re-configure when modified
config.reconfig_deps = []

# Optional numeric ID for decomp.me preset
# Can be overridden in libraries or objects
config.scratch_preset_id = None

# Base flags, common to most GC/Wii games.
# Generally leave untouched, with overrides added below.
cflags_base = [
    "-O2",
    # "-Wall",
    "-I include",
    "-I src",
    "-I src/Speed/GameCube/bWare/GameCube/dolphinsdk/include",
    "-I include/libc",
    "-DTARGET_GC",
    f"-I build/{config.version}/include",
    f"-DBUILD_VERSION={version_num}",
    f"-DVERSION_{config.version}",
]

# Debug flags
if args.debug:
    # Or -sym dwarf-2 for Wii compilers
    cflags_base.extend(["-gdwarf", "-DDEBUG=1"])
else:
    cflags_base.append("-DNDEBUG=1")

cflags_game = [*cflags_base, "-mps-nodf", "-mfast-cast"]

# Metrowerks library flags
cflags_runtime = [*cflags_base]

cflags_odemuexi = [*cflags_base]

cflags_amcstub = [*cflags_base]

cflags_libc = [*cflags_base]

config.linker_version = "ProDG/3.9.3"


# Helper function for Dolphin libraries
def DolphinLib(lib_name: str, objects: List[Object]) -> Dict[str, Any]:
    return {
        "lib": lib_name,
        "toolchain_version": "ProDG/3.9.3",
        "cflags": cflags_base,
        "progress_category": "sdk",
        "objects": objects,
    }


Matching = True  # Object matches and should be linked
NonMatching = False  # Object does not match and should not be linked
Equivalent = (
    config.non_matching
)  # Object should be linked when configured with --non-matching


# Object is only matching for specific versions
def MatchingFor(*versions):
    return config.version in versions


config.warn_missing_config = True
config.warn_missing_source = False
config.libs = [
    {
        "lib": "Game",
        "toolchain_version": config.linker_version,
        "cflags": cflags_game,
        "host": False,
        "progress_category": "game",  # str | List[str]
        "objects": [
            Object(NonMatching, "Speed/GameCube/Src/Ecstasy/EcstasyE.cpp"),
            Object(NonMatching, "Speed/GameCube/Src/Ecstasy/EcstasyEx.cpp"),
            Object(NonMatching, "Speed/GameCube/Src/Ecstasy/eLightE.cpp"),
            Object(NonMatching, "Speed/GameCube/Src/Ecstasy/eEnvMapE.cpp"),
            Object(NonMatching, "Speed/GameCube/Src/Ecstasy/eMathE.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Ecstasy/eMatrixE.cpp"),
            Object(NonMatching, "Speed/GameCube/Src/Ecstasy/ePShader.cpp"),
            Object(NonMatching, "Speed/GameCube/Src/Ecstasy/eVShader.cpp"),
            Object(NonMatching, "Speed/GameCube/Src/Ecstasy/eStrip.cpp"),
            Object(NonMatching, "Speed/GameCube/Src/Ecstasy/eSolidPlat.cpp"),
            Object(NonMatching, "Speed/GameCube/Src/Ecstasy/eViewPlat.cpp"),
            Object(NonMatching, "Speed/GameCube/Src/Platform.cpp"),
            Object(NonMatching, "Speed/GameCube/Src/Ecstasy/TextureInfoPlat.cpp"),
            Object(NonMatching, "Speed/GameCube/Src/Render/screenshot.cpp"),
            Object(NonMatching, "Speed/GameCube/Src/JoyE.cpp"),
            Object(NonMatching, "Speed/GameCube/Render/bba_com.cpp"),
            Object(NonMatching, "Speed/GameCube/Render/AcidFXE.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Misc/DemoDisc.cpp"),
            Object(NonMatching, "Speed/GameCube/Src/MovieE.cpp"),
            Object(NonMatching, "Speed/GameCube/Src/Logitech/Wheels.cpp"),
            Object(NonMatching, "Speed/GameCube/Src/Logitech/Ramp.cpp"),
            Object(NonMatching, "Speed/GameCube/Src/Logitech/Periodic.cpp"),
            Object(NonMatching, "Speed/GameCube/Src/Logitech/LGWheels.cpp"),
            Object(NonMatching, "Speed/GameCube/Src/Logitech/Force.cpp"),
            Object(NonMatching, "Speed/GameCube/Src/Logitech/Constant.cpp"),
            Object(NonMatching, "Speed/GameCube/Src/Logitech/Condition.cpp"),
            Object(NonMatching, "Speed/Indep/Src/EAXSound/RealStream/Src/Stream.cpp"),
            Object(
                NonMatching,
                "Speed/Indep/Src/Frontend/MenuScreens/Ingame/FEPkg_MU_OnlineDialogBox.cpp",
            ),
            Object(
                NonMatching,
                "Speed/Indep/Src/Frontend/MenuScreens/Ingame/FEPkg_MU_Keyboard.cpp",
            ),
            Object(NonMatching, "Speed/GameCube/Src/MemoryCard/GC_MemoryCard.cpp"),
            Object(NonMatching, "Speed/Indep/Src/World/World.cpp"),
            Object(NonMatching, "Speed/Indep/Src/World/RaceCoordinator.cpp"),
            Object(NonMatching, "Speed/Indep/Src/World/Car.cpp"),
            Object(NonMatching, "Speed/Indep/Src/World/Player.cpp"),
            Object(NonMatching, "Speed/Indep/Src/World/RaceParameters.cpp"),
            Object(NonMatching, "Speed/Indep/Src/World/StylePoints.cpp"),
            Object(NonMatching, "Speed/Indep/Src/World/OnlineManager.cpp"),
            Object(NonMatching, "Speed/Indep/Src/World/DriftManager.cpp"),
            Object(NonMatching, "Speed/Indep/Src/World/MiscStyleManager.cpp"),
            Object(NonMatching, "Speed/Indep/Src/World/Track.cpp"),
            Object(NonMatching, "Speed/Indep/Src/World/TrackInfo.cpp"),
            Object(NonMatching, "Speed/Indep/Src/World/TrackRoute.cpp"),
            Object(NonMatching, "Speed/Indep/Src/World/TrackRouteEditor.cpp"),
            Object(NonMatching, "Speed/Indep/Src/World/TrackPath.cpp"),
            Object(NonMatching, "Speed/Indep/Src/World/TrackStreamer.cpp"),
            Object(NonMatching, "Speed/Indep/Src/World/Scenery.cpp"),
            Object(NonMatching, "Speed/Indep/Src/World/VisibleSection.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Misc/Main.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Misc/SpeedChunks.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Misc/ResourceLoader.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Misc/GameFlow.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Misc/BuildRegionAmerica.cpp"),
            Object(NonMatching, "Speed/Indep/Src/AI/AICarController.cpp"),
            Object(NonMatching, "Speed/Indep/Src/AI/AIPlan.cpp"),
            Object(NonMatching, "Speed/Indep/Src/AI/AIUtil.cpp"),
            Object(NonMatching, "Speed/Indep/Src/AI/CollisionPredictor.cpp"),
            Object(NonMatching, "Speed/Indep/Src/AI/CarController.cpp"),
            Object(NonMatching, "Speed/Indep/Src/AI/DriveTarget.cpp"),
            Object(NonMatching, "Speed/Indep/Src/AI/DrivingChoice.cpp"),
            Object(NonMatching, "Speed/Indep/Src/AI/DragController.cpp"),
            Object(NonMatching, "Speed/Indep/Src/AI/PsychoDriver.cpp"),
            Object(NonMatching, "Speed/Indep/Src/AI/DragDriver.cpp"),
            Object(NonMatching, "Speed/Indep/Src/AI/RealDriver.cpp"),
            Object(NonMatching, "Speed/Indep/Src/AI/AIDriver.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Physics/Aerodynamics.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Physics/BeltMover.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Physics/Dynamics/CarState.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Physics/Dynamics/Collision.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Physics/Dynamics/CollisionBody.cpp"),
            Object(
                NonMatching, "Speed/Indep/Src/Physics/Behaviors/ComponentPhysics.cpp"
            ),
            Object(NonMatching, "Speed/Indep/Src/Physics/Behaviors/Contact.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Physics/Behaviors/Engine.cpp"),
            Object(NonMatching, "Speed/GJKsimplex.cpp"),
            Object(NonMatching, "Speed/GJKCollision.cpp"),
            Object(NonMatching, "Speed/GJKPolyhedron.cpp"),
            Object(NonMatching, "Speed/Integrable.cpp"),
            Object(NonMatching, "Speed/MellowMover.cpp"),
            Object(NonMatching, "Speed/PhysicsMover.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Animation/AnimBank.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Animation/AnimCtrl.cpp"),
            Object(NonMatching, "Speed/AnimEAGLBridge.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Animation/AnimPart.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Animation/AnimSkeleton.cpp"),
            Object(NonMatching, "Speed/NFSAnimCtrl.cpp"),
            Object(NonMatching, "Speed/NFSAnimInit.cpp"),
            Object(NonMatching, "Speed/NFSAnimBank.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Camera/Camera.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Camera/CameraCoordinator.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Camera/DragData.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Camera/CameraMover.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Camera/ZoneCameras.cpp"),
            Object(
                NonMatching,
                "Speed/Indep/Src/Frontend/MenuScreens/Ingame/FEPkg_Options.cpp",
            ),
            Object(
                NonMatching,
                "Speed/Indep/Src/Frontend/MenuScreens/Ingame/FEPkg_PauseMenu.cpp",
            ),
            Object(
                NonMatching,
                "Speed/Indep/Src/Frontend/MenuScreens/Ingame/FEPkg_PreRace.cpp",
            ),
            Object(
                NonMatching,
                "Speed/Indep/Src/Frontend/MenuScreens/Ingame/FEPkg_PostRace.cpp",
            ),
            Object(NonMatching, "Speed/Indep/Src/Frontend/Hud/FEPkg_Hud.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Frontend/Database/FEDatabase.cpp"),
            Object(
                NonMatching,
                "Speed/Indep/Src/Frontend/MenuScreens/SafeHouse/FEPkg_GarageMain.cpp",
            ),
            Object(
                NonMatching,
                "Speed/Indep/Src/Frontend/MenuScreens/SafeHouse/FEPkg_MU_Main.cpp",
            ),
            Object(
                NonMatching,
                "Speed/Indep/Src/Frontend/MenuScreens/SafeHouse/QuickRace/FEPkg_MU_QuickRaceModeSelect.cpp",
            ),
            Object(
                NonMatching,
                "Speed/Indep/Src/Frontend/MenuScreens/SafeHouse/QuickRace/FEPkg_MU_QuickRaceOptions.cpp",
            ),
            Object(
                NonMatching,
                "Speed/Indep/Src/Frontend/MenuScreens/SafeHouse/QuickRace/FEPkg_MU_QuickRaceTrackSelect.cpp",
            ),
            Object(
                NonMatching,
                "Speed/Indep/Src/Frontend/MenuScreens/SafeHouse/QuickRace/FEPkg_MU_QuickRaceCarSelect.cpp",
            ),
            Object(
                NonMatching,
                "Speed/Indep/Src/Frontend/MenuScreens/SafeHouse/QuickRace/FEPkg_MU_QuickRaceLapPopup.cpp",
            ),
            Object(
                NonMatching,
                "Speed/Indep/Src/Frontend/MenuScreens/SafeHouse/QuickRace/FEPkg_MU_PauseOptions.cpp",
            ),
            Object(NonMatching, "Speed/Indep/Src/Frontend/MenuScreens/CarSelect.cpp"),
            Object(
                NonMatching,
                "Speed/Indep/Src/Frontend/MenuScreens/FEpkg_UndergroundTradeCar.cpp",
            ),
            Object(
                NonMatching,
                "Speed/Indep/Src/Frontend/MenuScreens/FEPkg_UndergroundChooseCar.cpp",
            ),
            Object(
                NonMatching,
                "Speed/Indep/Src/Frontend/MenuScreens/FEPkg_UndergroundStatusStuff.cpp",
            ),
            Object(
                NonMatching,
                "Speed/Indep/Src/Frontend/MenuScreens/FEPkg_UndergroundMapScreen.cpp",
            ),
            Object(
                NonMatching,
                "Speed/Indep/Src/Frontend/MenuScreens/FEPkg_MU_MainMenuCarCustomize.cpp",
            ),
            Object(
                NonMatching,
                "Speed/Indep/Src/Frontend/MenuScreens/FEPkg_MemcardPrompter.cpp",
            ),
            Object(
                NonMatching,
                "Speed/Indep/Src/Frontend/MenuScreens/FEpkg_UndergroundJunkmanSamanthaUnique.cpp",
            ),
            Object(
                NonMatching,
                "Speed/Indep/Src/Frontend/MenuScreens/FEPkg_ChooseUserProfile.cpp",
            ),
            Object(
                NonMatching,
                "Speed/Indep/Src/Frontend/MenuScreens/FEng_SoundShenanigans.cpp",
            ),
            Object(
                NonMatching, "Speed/Indep/Src/Frontend/MenuScreens/FEPkg_MU_Pause.cpp"
            ),
            Object(
                NonMatching, "Speed/Indep/Src/Frontend/MenuScreens/FEPkg_MU_Options.cpp"
            ),
            Object(
                NonMatching,
                "Speed/Indep/Src/Frontend/MenuScreens/FEPkg_MU_OptionsController.cpp",
            ),
            Object(
                NonMatching,
                "Speed/Indep/Src/Frontend/MenuScreens/FEPkg_MU_OptionsHUD.cpp",
            ),
            Object(
                NonMatching,
                "Speed/Indep/Src/Frontend/MenuScreens/FEPkg_MU_ScreenPos.cpp",
            ),
            Object(
                NonMatching,
                "Speed/Indep/Src/Frontend/MenuScreens/Ingame/FEPkg_Chyron.cpp",
            ),
            Object(
                NonMatching,
                "Speed/Indep/Src/Frontend/MenuScreens/Ingame/FEPkg_Loading.cpp",
            ),
            Object(
                NonMatching,
                "Speed/Indep/Src/Frontend/MenuScreens/Ingame/FEPkg_ColorPicker.cpp",
            ),
            Object(
                NonMatching,
                "Speed/Indep/Src/Frontend/MenuScreens/Ingame/FEPkg_ConfirmDialog.cpp",
            ),
            Object(
                NonMatching,
                "Speed/Indep/Src/Frontend/MenuScreens/Ingame/FEPkg_InfoDialog.cpp",
            ),
            Object(
                NonMatching, "Speed/Indep/Src/Frontend/MenuScreens/FEPkg_MU_MPLogin.cpp"
            ),
            Object(
                NonMatching,
                "Speed/Indep/Src/Frontend/MenuScreens/Ingame/FEPkg_MU_MultiplayerCarSelect.cpp",
            ),
            Object(
                NonMatching,
                "Speed/Indep/Src/Frontend/MenuScreens/Ingame/FEPkg_MU_MPChooseGarage.cpp",
            ),
            Object(
                NonMatching,
                "Speed/Indep/Src/Frontend/MenuScreens/Ingame/FEPkg_VinylShop.cpp",
            ),
            Object(
                NonMatching,
                "Speed/Indep/Src/Frontend/MenuScreens/Ingame/StatsScreen.cpp",
            ),
            Object(
                NonMatching,
                "Speed/Indep/Src/Frontend/MenuScreens/Ingame/FEPkg_ONL_WaitSync.cpp",
            ),
            Object(
                NonMatching,
                "Speed/Indep/Src/Frontend/MenuScreens/Ingame/FEpkg_MU_InGameTutorialScreen.cpp",
            ),
            Object(
                NonMatching,
                "Speed/Indep/Src/Frontend/MenuScreens/Ingame/FEPkg_PresetBrowser.cpp",
            ),
            Object(NonMatching, "Speed/Indep/Src/FEng/FEngine.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Frontend/FEngRender.cpp"),
            Object(NonMatching, "Speed/Indep/Src/FEng/FEngSpeedPackages.cpp"),
            Object(NonMatching, "Speed/Indep/Src/FEng/FEngStandard.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Frontend/FEngFont.cpp"),
            Object(
                NonMatching, "Speed/Indep/Src/Frontend/FEngInterfaces/FEngInterface.cpp"
            ),
            Object(NonMatching, "Speed/Indep/Src/Frontend/FEngFrontend.cpp"),
            Object(NonMatching, "Speed/Indep/Src/FEng/FEButtonMap.cpp"),
            Object(NonMatching, "Speed/Indep/Src/FEng/FECodeListBox.cpp"),
            Object(NonMatching, "Speed/Indep/Src/FEng/FEEvent.cpp"),
            Object(NonMatching, "Speed/Indep/Src/FEng/FEGroup.cpp"),
            Object(NonMatching, "Speed/Indep/Src/FEng/FEJoyPad.cpp"),
            Object(NonMatching, "Speed/Indep/Src/FEng/FEKeyInterp.cpp"),
            Object(NonMatching, "Speed/Indep/Src/FEng/FEKeyInterpLinear.cpp"),
            Object(NonMatching, "Speed/Indep/Src/FEng/FEKeyInterpNone.cpp"),
            Object(NonMatching, "Speed/Indep/Src/FEng/FEKeyTrack.cpp"),
            Object(NonMatching, "Speed/Indep/Src/FEng/FEList.cpp"),
            Object(NonMatching, "Speed/Indep/Src/FEng/FEMessageResponse.cpp"),
            Object(NonMatching, "Speed/Indep/Src/FEng/FEMsgTargetList.cpp"),
            Object(NonMatching, "Speed/Indep/Src/FEng/FEObject.cpp"),
            Object(NonMatching, "Speed/Indep/Src/FEng/FEPackage.cpp"),
            Object(NonMatching, "Speed/Indep/Src/FEng/FEPackageList.cpp"),
            Object(NonMatching, "Speed/Indep/Src/FEng/FEPackageReader.cpp"),
            Object(NonMatching, "Speed/Indep/Src/FEng/FEScript.cpp"),
            Object(NonMatching, "Speed/Indep/Src/FEng/FESlotPool.cpp"),
            Object(NonMatching, "Speed/Indep/Src/FEng/FETypeLib.cpp"),
            Object(NonMatching, "Speed/Indep/Src/FEng/FETypeNode.cpp"),
            Object(NonMatching, "Speed/Indep/Src/FEng/FETypes.cpp"),
            Object(
                NonMatching,
                "Speed/Indep/Src/Frontend/MenuScreens/Ingame/FEPkg_PartsBrowser.cpp",
            ),
            Object(NonMatching, "Speed/Indep/Src/FEng/FERefList.cpp"),
            Object(NonMatching, "Speed/Indep/Src/FEng/FEString.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Frontend/FERenderObject.cpp"),
            Object(NonMatching, "Speed/Indep/Src/FEng/FEMouse.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Debug/ScreenPrintf.cpp"),
            Object(NonMatching, "Speed/Indep/Src/FEng/FEng_Magazines.cpp"),
            Object(NonMatching, "Speed/MagazineDatabase.cpp"),
            Object(NonMatching, "Speed/MagazineTextureHandler.cpp"),
            Object(NonMatching, "Speed/WideDecalManager.cpp"),
            Object(NonMatching, "Speed/Indep/Src/EAXSound/EAXSound.cpp"),
            Object(NonMatching, "Speed/Indep/Src/EAXSound/EAXAemsManager.cpp"),
            Object(NonMatching, "Speed/Indep/Src/EAXSound/EAXMod.cpp"),
            Object(NonMatching, "Speed/Indep/Src/EAXSound/EAXFrontEnd.cpp"),
            Object(NonMatching, "Speed/Indep/Src/EAXSound/EAXAITunerCar.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Audio/SFXCtl/EVTSYS_ENVIRO.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Audio/SFXCtl/EVTSYS_TURBO.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Audio/SFXCtl/EVTSYS_FE.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Audio/SFXCtl/COLLISION_EVTS.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Audio/SFXCtl/ENGINE_EVTSYS.cpp"),
            Object(NonMatching, "Speed/Indep/Src/EAXSound/EAXTrafficCar.cpp"),
            Object(NonMatching, "Speed/Indep/Src/EAXSound/EAXTunerCar.cpp"),
            Object(NonMatching, "Speed/Indep/Src/EAXSound/EAXCar.cpp"),
            Object(NonMatching, "Speed/Indep/Src/EAXSound/EAX3DS.cpp"),
            Object(NonMatching, "Speed/Indep/Src/EAXSound/EAXCollision.cpp"),
            Object(NonMatching, "Speed/Indep/Src/EAXSound/EAXSND8Wrapper.cpp"),
            Object(NonMatching, "Speed/Indep/Src/EAXSound/EAXSndTweakData.cpp"),
            Object(NonMatching, "Speed/Indep/bWare/Src/bCrc32.cpp"),
            Object(NonMatching, "Speed/SoundObject.cpp"),
            Object(NonMatching, "Speed/Indep/Src/EAXSound/EAXEnvironment.cpp"),
            Object(NonMatching, "Speed/Indep/Src/EAXSound/EAXMixer.cpp"),
            Object(NonMatching, "Speed/Indep/Src/EAXSound/EAXPresets.cpp"),
            Object(
                NonMatching, "Speed/Indep/Src/EAXSound/Stream/EAXS_StreamManager.cpp"
            ),
            Object(
                NonMatching, "Speed/Indep/Src/EAXSound/Stream/EAXS_StreamControl.cpp"
            ),
            Object(NonMatching, "Speed/Indep/Src/EAXSound/Stream/EAXS_Streams.cpp"),
            Object(
                NonMatching, "Speed/Indep/Src/EAXSound/Stream/EAXS_AmbMonoStream.cpp"
            ),
            Object(
                NonMatching, "Speed/Indep/Src/EAXSound/Stream/EAXS_AmbStereoStream.cpp"
            ),
            Object(NonMatching, "Speed/Indep/Src/EAXSound/Stream/EAXS_MusicStream.cpp"),
            Object(
                NonMatching, "Speed/Indep/Src/EAXSound/Stream/EAXS_TCMonoStream.cpp"
            ),
            Object(
                NonMatching, "Speed/Indep/Src/EAXSound/Stream/EAXS_SpeechStream.cpp"
            ),
            Object(NonMatching, "Speed/Indep/Src/Ecstasy/Ecstasy.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Ecstasy/eStreamingPack.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Ecstasy/eModel.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Ecstasy/eSolid.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Ecstasy/eLight.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Ecstasy/eView.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Ecstasy/Texture.cpp"),
            Object(NonMatching, "Speed/Indep/Src/World/Sun.cpp"),
            Object(NonMatching, "Speed/Indep/bWare/Src/bDebug.cpp"),
            Object(NonMatching, "Speed/Indep/bWare/Src/bFunkServer.cpp"),
            Object(NonMatching, "Speed/Indep/bWare/Src/bInventory.cpp"),
            Object(NonMatching, "Speed/Indep/bWare/Src/bList.cpp"),
            Object(NonMatching, "Speed/Indep/bWare/Src/bMath.cpp"),
            Object(NonMatching, "Speed/Indep/bWare/Src/bMatrix.cpp"),
            Object(NonMatching, "Speed/Indep/bWare/Src/bMemCpy.cpp"),
            Object(NonMatching, "Speed/Indep/bWare/Src/bMemory.cpp"),
            Object(NonMatching, "Speed/Indep/bWare/Src/bPrintf.cpp"),
            Object(NonMatching, "Speed/Indep/bWare/Src/bQuaternion.cpp"),
            Object(NonMatching, "Speed/Indep/bWare/Src/bSlotPool.cpp"),
            Object(NonMatching, "Speed/Indep/bWare/Src/bVector.cpp"),
            Object(NonMatching, "Speed/Indep/bWare/Src/Strings.cpp"),
            Object(NonMatching, "Speed/SpeedGlobal_.cpp"),
            Object(NonMatching, "Speed/NFSU_Streams.cpp"),
            Object(
                NonMatching,
                "Speed/Indep/Src/Frontend/MenuScreens/Ingame/FEPkg_MapScreen.cpp",
            ),
            Object(NonMatching, "Speed/Indep/Src/Misc/Config.cpp"),
            Object(NonMatching, "Speed/Indep/Src/World/CarRender.cpp"),
            Object(NonMatching, "Speed/Indep/Src/World/SkyRender.cpp"),
            Object(NonMatching, "Speed/Replay.cpp"),
            Object(NonMatching, "Speed/DemoModeReplay.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Misc/Joystick.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Misc/Rumble.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Physics/TrafficMover.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Physics/PhysicsUpgrades.cpp"),
            Object(NonMatching, "Speed/Indep/Src/World/MobileTopology.cpp"),
            Object(NonMatching, "Speed/Indep/Src/World/WorldEntity.cpp"),
            Object(NonMatching, "Speed/Indep/Src/World/WorldObject.cpp"),
            Object(NonMatching, "Speed/Indep/Src/World/Mover.cpp"),
            Object(NonMatching, "Speed/Indep/Src/World/SpaceNode.cpp"),
            Object(NonMatching, "Speed/Indep/Src/World/SpaceCase.cpp"),
            Object(NonMatching, "Speed/Indep/Src/World/SpaceCadet.cpp"),
            Object(NonMatching, "Speed/Indep/Src/World/AnimationMover.cpp"),
            Object(NonMatching, "Speed/Indep/Src/World/CarWorldObject.cpp"),
            Object(NonMatching, "Speed/Indep/Src/World/Avoidable.cpp"),
            Object(NonMatching, "Speed/Indep/Src/World/SomeWorldObjects.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Misc/Joylog.cpp"),
            Object(NonMatching, "Speed/Indep/Src/World/CarInfo.cpp"),
            Object(NonMatching, "Speed/Indep/Src/World/CarPartNames.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Misc/Spline.cpp"),
            Object(NonMatching, "Speed/TrafficController.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Misc/Table.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Physics/Behaviors/RigidBody.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Misc/Timer.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Physics/Core/Wheel.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Physics/Core/Suspension.cpp"),
            Object(NonMatching, "Speed/Indep/Src/World/WeatherMan.cpp"),
            Object(NonMatching, "Speed/Indep/Src/World/fogvolume.cpp"),
            Object(NonMatching, "Speed/Indep/Src/World/Skids.cpp"),
            Object(NonMatching, "Speed/Indep/Src/World/Clans.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Misc/QueuedFile.cpp"),
            Object(NonMatching, "Speed/Indep/Src/World/CarLoader.cpp"),
            Object(NonMatching, "Speed/NIS.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Misc/LZCompress.cpp"),
            Object(NonMatching, "Speed/Indep/Src/World/BodyDamage.cpp"),
            Object(NonMatching, "Speed/Indep/Src/World/CarDamage.cpp"),
            Object(NonMatching, "Speed/Indep/Src/World/EventManager.cpp"),
            Object(NonMatching, "Speed/Indep/Src/World/TrackMap.cpp"),
            Object(NonMatching, "Speed/Indep/Src/World/SrcWorldModel.cpp"),
            Object(NonMatching, "Speed/Indep/Src/World/TerrainType.cpp"),
            Object(NonMatching, "Speed/Indep/Src/World/WorldObjectCollisionBody.cpp"),
            Object(NonMatching, "Speed/Indep/Src/World/CharacterInfo.cpp"),
            Object(NonMatching, "Speed/Indep/Src/World/Subworld.cpp"),
            Object(NonMatching, "Speed/Indep/Src/World/FernFlattener.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Misc/bRepeat.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Misc/bFile.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Misc/bMemoryOverloads.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Misc/Print3d.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Misc/DebugTopology.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Misc/Polyhedra.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Misc/Smokeable.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Misc/TerrainEffects.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Misc/TrafficTeleporter.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Misc/DrivingLocation.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Misc/TrackedController.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Misc/RealController.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Misc/QuickSpline.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Misc/Stomper.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Misc/EasterEggs.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Misc/Elipse.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Misc/base64.c"),
            Object(
                NonMatching, "Speed/Indep/Src/Frontend/MenuScreens/Common/Slider.cpp"
            ),
            Object(NonMatching, "Speed/Indep/Src/Frontend/Localization/Localize.cpp"),
            Object(NonMatching, "Speed/CareerMode.cpp"),
            Object(NonMatching, "Speed/RCMP_Player.cpp"),
            Object(NonMatching, "Speed/NFSSkeleton.cpp"),
            Object(NonMatching, "Speed/FuturePoints.cpp"),
            Object(NonMatching, "Speed/Indep/Src/World/NeuQuant.cpp"),
            Object(NonMatching, "Speed/Indep/Src/World/CarSkin.cpp"),
            Object(NonMatching, "Speed/Indep/Src/Frontend/SubTitle.cpp"),
            Object(NonMatching, "Speed/Indep/Src/EAGL4Anim/dlopen.cpp"),
            Object(NonMatching, "Speed/Indep/Src/EAGL4Anim/conspool.cpp"),
            Object(NonMatching, "Speed/SingleDrawGouraud.cpp"),
            Object(NonMatching, "Speed/SingleDrawTexture.cpp"),
            Object(NonMatching, "Speed/Indep/Src/EAGL4Anim/printmessage.cpp"),
            Object(NonMatching, "Speed/Indep/Src/EAGL4Anim/sympool.cpp"),
            Object(NonMatching, "Speed/Indep/Src/EAGL4Anim/Skeleton.cpp"),
            Object(NonMatching, "Speed/Indep/Src/EAGL4Anim/System.cpp"),
            Object(NonMatching, "Speed/Indep/Src/EAGL4Anim/SystemCmn.cpp"),
            Object(NonMatching, "Speed/Indep/Src/EAGL4Anim/ScratchBuffer.cpp"),
            Object(NonMatching, "Speed/Indep/Src/EAGL4Anim/MemoryPoolManager.cpp"),
            Object(NonMatching, "Speed/Indep/Src/EAGL4Anim/RawStateChan.cpp"),
            Object(NonMatching, "Speed/Indep/Src/EAGL4Anim/AnimBank.cpp"),
            Object(NonMatching, "Speed/Indep/Src/EAGL4Anim/FnAnimMemoryMap.cpp"),
            Object(NonMatching, "Speed/Indep/Src/EAGL4Anim/CompoundChannel.cpp"),
            Object(NonMatching, "Speed/Indep/Src/EAGL4Anim/FnDeltaQFast.cpp"),
            Object(NonMatching, "Speed/Indep/Src/EAGL4Anim/FnDeltaF3.cpp"),
            Object(NonMatching, "Speed/Indep/Src/EAGL4Anim/FnDeltaQ.cpp"),
            Object(NonMatching, "Speed/Indep/Src/EAGL4Anim/FnDeltaF1.cpp"),
            Object(NonMatching, "Speed/Indep/Src/EAGL4Anim/FnDeltaSingleQ.cpp"),
            Object(NonMatching, "Speed/Indep/Src/EAGL4Anim/DeltaChan.cpp"),
            Object(NonMatching, "Speed/Indep/Src/EAGL4Anim/DeltaCompressedData.cpp"),
            Object(NonMatching, "Speed/Indep/Src/EAGL4Anim/FnEventBlender.cpp"),
            Object(NonMatching, "Speed/Indep/Src/EAGL4Anim/RawPoseChannel.cpp"),
            Object(NonMatching, "Speed/Indep/Src/EAGL4Anim/StatelessQ.cpp"),
            Object(NonMatching, "Speed/Indep/Src/EAGL4Anim/StatelessF3.cpp"),
            Object(NonMatching, "Speed/Indep/Src/EAGL4Anim/RawEventChannel.cpp"),
            Object(NonMatching, "Speed/Indep/Src/EAGL4Anim/FnRunBlender.cpp"),
            Object(NonMatching, "Speed/Indep/Src/EAGL4Anim/FnTurnBlender.cpp"),
            Object(NonMatching, "Speed/Indep/Src/EAGL4Anim/FnStatelessQ.cpp"),
            Object(NonMatching, "Speed/Indep/Src/EAGL4Anim/FnStatelessF3.cpp"),
        ],
    },
    {
        "lib": "rcmp",
        "toolchain_version": config.linker_version,
        "cflags": cflags_game,
        "host": False,
        "progress_category": "libs",  # str | List[str]
        "objects": [
            Object(NonMatching, "egami/rcmp/dev/source/decoder/cmn/rcmpbase.cpp"),
            Object(NonMatching, "egami/rcmp/dev/source/decoder/cmn/rcmp2real.cpp"),
            Object(NonMatching, "egami/rcmp/dev/source/decoder/cmn/rcmp_mad_codec.cpp"),
            Object(
                NonMatching,
                "egami/rcmp/dev/source/decoder/cmn/rcmp_mad_codec_chunk_types.cpp",
            ),
            Object(NonMatching, "egami/rcmp/dev/source/decoder/cmn/maddec.cpp"),
            Object(NonMatching, "egami/rcmp/dev/source/decoder/cmn/maddeca.cpp"),
            Object(NonMatching, "egami/rcmp/dev/source/decoder/cmn/madidct.cpp"),
        ],
    },
    {
        "lib": "realgraph",
        "toolchain_version": config.linker_version,
        "cflags": cflags_game,
        "host": False,
        "progress_category": "libs",  # str | List[str]
        "objects": [
            Object(NonMatching, "egami/realgraph/source/shape/cmn/shpclut.cpp"),
            Object(NonMatching, "egami/realgraph/source/shape/cmn/shpdepth.cpp"),
            Object(NonMatching, "egami/realgraph/source/shape/cmn/shpdestroy.cpp"),
            Object(NonMatching, "egami/realgraph/source/shape/cmn/shpisclut.cpp"),
            Object(NonMatching, "egami/realgraph/source/shape/cmn/shpmemalloc.cpp"),
            Object(NonMatching, "egami/realgraph/source/shape/cmn/shpsize.cpp"),
        ],
    },
    {
        "lib": "snd",
        "toolchain_version": config.linker_version,
        "cflags": cflags_game,
        "host": False,
        "progress_category": "libs",  # str | List[str]
        "objects": [
            Object(NonMatching, "snd/source/library/cmn/saems.c"),
            Object(NonMatching, "snd/source/library/cmn/saemsamb.c"),
            Object(NonMatching, "snd/source/library/cmn/saemsstr.c"),
            Object(NonMatching, "snd/source/library/cmn/saemstimupdt.c"),
            Object(NonMatching, "snd/source/library/cmn/salloc.c"),
            Object(NonMatching, "snd/source/library/cmn/sbadd.c"),
            Object(NonMatching, "snd/source/library/cmn/ssballoc.c"),
            Object(NonMatching, "snd/source/library/cmn/ssbhdrcpy.c"),
            Object(NonMatching, "snd/source/library/cmn/ssbhdrsze.c"),
            Object(NonMatching, "snd/source/library/cmn/ssbplay.c"),
            Object(NonMatching, "snd/source/library/cmn/ssbremove.c"),
            Object(NonMatching, "snd/source/library/cmn/ssbvalid.c"),
            Object(NonMatching, "snd/source/library/gc/sscalcfx.c"),
            Object(NonMatching, "snd/source/library/gc/ssdfx.c"),
            Object(NonMatching, "snd/source/library/gc/sdspmix.c"),
            Object(NonMatching, "snd/source/library/cmn/seffect.c"),
            Object(NonMatching, "snd/source/library/cmn/sevent.cpp"),
            Object(NonMatching, "snd/source/library/cmn/sfxlevel.c"),
            Object(NonMatching, "snd/source/library/mix/sfxrevc.c"),
            Object(NonMatching, "snd/source/library/cmn/sgetdata.c"),
            Object(NonMatching, "snd/source/library/cmn/sinitdts.c"),
            Object(NonMatching, "snd/source/library/cmn/smemcpy.c"),
            Object(NonMatching, "snd/source/library/cmn/smemman.c"),
            Object(NonMatching, "snd/source/library/mix/smixer.c"),
            Object(NonMatching, "snd/source/library/gc/snddrv.c"),
            Object(NonMatching, "snd/source/library/cmn/spatkey.c"),
            Object(NonMatching, "snd/source/library/cmn/spitch.c"),
            Object(NonMatching, "snd/source/library/cmn/spktplay.c"),
            Object(NonMatching, "snd/source/library/cmn/splysdef.c"),
            Object(NonMatching, "snd/source/library/cmn/spoutlat.c"),
            Object(NonMatching, "snd/source/library/cmn/srandom.c"),
            Object(NonMatching, "snd/source/library/cmn/srender.c"),
            Object(NonMatching, "snd/source/library/cmn/sresopat.c"),
            Object(NonMatching, "snd/source/library/cmn/sserver.c"),
            Object(NonMatching, "snd/source/library/cmn/ssine.c"),
            Object(NonMatching, "snd/source/library/cmn/sst.c"),
            Object(NonMatching, "snd/source/library/cmn/sst3dpos.c"),
            Object(NonMatching, "snd/source/library/cmn/sstcrtap.c"),
            Object(NonMatching, "snd/source/library/cmn/sstfxlev.c"),
            Object(NonMatching, "snd/source/library/cmn/sstgetrp.c"),
            Object(NonMatching, "snd/source/library/cmn/ssthighp.c"),
            Object(NonMatching, "snd/source/library/cmn/ssthold.c"),
            Object(NonMatching, "snd/source/library/cmn/sstlowp.c"),
            Object(NonMatching, "snd/source/library/cmn/sstop.c"),
            Object(NonMatching, "snd/source/library/cmn/sstovrhd.c"),
            Object(NonMatching, "snd/source/library/cmn/sstpmult.c"),
            Object(NonMatching, "snd/source/library/cmn/sstqreqi.c"),
            Object(NonMatching, "snd/source/library/cmn/sstrmdry.cpp"),
            Object(NonMatching, "snd/source/library/cmn/sstrstat.c"),
            Object(NonMatching, "snd/source/library/cmn/sstsetgl.c"),
            Object(NonMatching, "snd/source/library/cmn/sststat.c"),
            Object(NonMatching, "snd/source/library/cmn/ssttmul.c"),
            Object(NonMatching, "snd/source/library/cmn/sstvol.c"),
            Object(NonMatching, "snd/source/library/cmn/ssys.cpp"),
            Object(NonMatching, "snd/source/library/cmn/ssysinit.c"),
            Object(NonMatching, "snd/source/library/cmn/ssysserv.c"),
            Object(NonMatching, "snd/source/library/cmn/ssysveccsismutex.cpp"),
            Object(NonMatching, "snd/source/library/cmn/stagpat.c"),
            Object(NonMatching, "snd/source/library/cmn/stimemul.c"),
            Object(NonMatching, "snd/source/library/cmn/stpparse.c"),
            Object(NonMatching, "snd/source/library/mix/stretch.c"),
            Object(NonMatching, "snd/source/library/cmn/svecreal.cpp"),
            Object(NonMatching, "snd/source/library/cmn/svol.c"),
            Object(NonMatching, "snd/source/library/mix/sx87d16.c"),
            Object(NonMatching, "snd/source/library/extern/coda/cmn/coda.cpp"),
            Object(NonMatching, "snd/source/library/cmn/s3dlow.c"),
            Object(NonMatching, "snd/source/library/gc/saramman.c"),
            Object(NonMatching, "snd/source/library/cmn/satospkr.c"),
            Object(NonMatching, "snd/source/library/cmn/sclcptch.c"),
            Object(NonMatching, "snd/source/library/cmn/sctlfilt.c"),
            Object(NonMatching, "snd/source/library/cmn/sctrldry.cpp"),
            Object(NonMatching, "snd/source/library/cmn/sdownmix.cpp"),
            Object(NonMatching, "snd/source/library/mix/sfamplf.c"),
            Object(NonMatching, "snd/source/library/mix/sfbpffir8.c"),
            Object(NonMatching, "snd/source/library/mix/sfecho.c"),
            Object(NonMatching, "snd/source/library/mix/sfft24.c"),
            Object(NonMatching, "snd/source/library/mix/sfhpffir8.c"),
            Object(NonMatching, "snd/source/library/mix/sfilter.c"),
            Object(NonMatching, "snd/source/library/mix/sfir.c"),
            Object(NonMatching, "snd/source/library/mix/sfir8.c"),
            Object(NonMatching, "snd/source/library/mix/sflpf.c"),
            Object(NonMatching, "snd/source/library/mix/sflpffir8.c"),
            Object(NonMatching, "snd/source/library/mix/sfmixer.c"),
            Object(NonMatching, "snd/source/library/mix/sfreson.c"),
            Object(NonMatching, "snd/source/library/mix/sfsplit.c"),
            Object(NonMatching, "snd/source/library/mix/sfsrc.c"),
            Object(NonMatching, "snd/source/library/cmn/sgettag.c"),
            Object(NonMatching, "snd/source/library/mix/shipass.c"),
            Object(NonMatching, "snd/source/library/mix/sinit16.c"),
            Object(NonMatching, "snd/source/library/mix/sinitut.c"),
            Object(NonMatching, "snd/source/library/mix/sinitxa.c"),
            Object(NonMatching, "snd/source/library/cmn/slib.c"),
            Object(NonMatching, "snd/source/library/cmn/slinklst.c"),
            Object(NonMatching, "snd/source/library/mix/slinkmix.c"),
            Object(NonMatching, "snd/source/library/cmn/slowpass.c"),
            Object(NonMatching, "snd/source/library/cmn/smemhigh.cpp"),
            Object(NonMatching, "snd/source/library/mix/smixc.c"),
            Object(NonMatching, "snd/source/library/mix/smixfram.c"),
            Object(NonMatching, "snd/source/library/mix/smixhip.c"),
            Object(NonMatching, "snd/source/library/mix/smixlowp.c"),
            Object(NonMatching, "snd/source/library/mix/smixptch.c"),
            Object(NonMatching, "snd/source/library/mix/smixtmul.c"),
            Object(NonMatching, "snd/source/library/cmn/SNDI_cos.c"),
            Object(NonMatching, "snd/source/library/cmn/SNDI_mult16.c"),
            Object(NonMatching, "snd/source/library/cmn/SNDI_root1x.c"),
            Object(NonMatching, "snd/source/library/cmn/SNDI_sin.c"),
            Object(NonMatching, "snd/source/library/cmn/sover.c"),
            Object(NonMatching, "snd/source/library/cmn/spantoaz.c"),
            Object(NonMatching, "snd/source/library/cmn/spat2hdr.c"),
            Object(NonMatching, "snd/source/library/cmn/spktctoh.c"),
            Object(NonMatching, "snd/source/library/cmn/srrange.c"),
            Object(NonMatching, "snd/source/library/cmn/sstopall.c"),
            Object(NonMatching, "snd/source/library/cmn/ssysreal.c"),
            Object(NonMatching, "snd/source/library/mix/supf.c"),
            Object(NonMatching, "snd/source/library/mix/suplf.c"),
            Object(NonMatching, "snd/source/library/mix/supmutf.c"),
            Object(NonMatching, "snd/source/library/mix/supmutlf.c"),
            Object(NonMatching, "snd/source/library/mix/supmutpf.c"),
            Object(NonMatching, "snd/source/library/mix/suppf.c"),
            Object(NonMatching, "snd/source/library/mix/supxaf.cpp"),
            Object(NonMatching, "snd/source/library/mix/supxalf.cpp"),
            Object(NonMatching, "snd/source/library/mix/supxapf.cpp"),
            Object(NonMatching, "snd/source/library/extern/coda/cmn/eaxadecf.cpp"),
            Object(NonMatching, "snd/source/library/extern/coda/cmn/mtdecf.cpp"),
            Object(NonMatching, "snd/source/library/cmn/sattrdef.c"),
            Object(NonMatching, "snd/source/library/cmn/sexithndl.c"),
            Object(NonMatching, "snd/source/library/mix/sfrsf.c"),
            Object(NonMatching, "snd/source/library/cmn/sgparse.cpp"),
            Object(NonMatching, "snd/source/library/cmn/SNDI_findprime.c"),
            Object(NonMatching, "snd/source/library/mix/scrsfl.c"),
        ],
    },
    {
        "lib": "realcore",
        "toolchain_version": config.linker_version,
        "cflags": cflags_game,
        "host": False,
        "progress_category": "libs",  # str | List[str]
        "objects": [
            Object(NonMatching, "realcore/source/input/cmn/device.cpp"),
            Object(NonMatching, "realcore/source/file/cmn/filesys.cpp"),
            Object(NonMatching, "realcore/source/file/cmn/filesysopts.cpp"),
            Object(NonMatching, "realcore/source/file/cmn/syncfile.cpp"),
            Object(NonMatching, "realcore/source/file/cmn/hlafile.cpp"),
            Object(NonMatching, "realcore/source/file/cmn/hlsfile.cpp"),
            Object(NonMatching, "realcore/source/system/cmn/timer.cpp"),
            Object(NonMatching, "realcore/source/system/cmn/systask.cpp"),
            Object(NonMatching, "realcore/source/system/gc/threads.cpp"),
            Object(NonMatching, "realcore/source/system/gc/signals.cpp"),
            Object(NonMatching, "realcore/source/system/debug/cmn/printstr.cpp"),
            Object(NonMatching, "realcore/source/system/debug/cmn/abortmsg.cpp"),
            Object(NonMatching, "realcore/source/std/cmn/memclear.cpp"),
            Object(NonMatching, "realcore/source/system/gc/timerthread.cpp"),
            Object(NonMatching, "realcore/source/system/gc/memfill.cpp"),
        ],
    },
    {
        "lib": "realmemcard",
        "toolchain_version": config.linker_version,
        "cflags": cflags_game,
        "host": False,
        "progress_category": "libs",  # str | List[str]
        "objects": [
            Object(NonMatching, "realmemcard/source/lib/gc/gc_interface.cpp"),
            Object(NonMatching, "realmemcard/source/lib/gc/public.cpp"),
            Object(NonMatching, "realmemcard/source/lib/gc/trctasks.cpp"),
            Object(NonMatching, "realmemcard/source/lib/gc/tasks.cpp"),
        ],
    },
    {
        "lib": "misc",
        "toolchain_version": config.linker_version,
        "cflags": cflags_game,
        "host": False,
        "progress_category": "libs",  # str | List[str]
        "objects": [
            Object(NonMatching, "crtE1.tmp"),
            Object(NonMatching, "ppc42.tmp"),
            Object(NonMatching, "fil14A.tmp"),
            Object(NonMatching, "pro14B.tmp"),
            Object(NonMatching, "FSasync.c"),
            Object(NonMatching, "sndvd.c"),
            Object(NonMatching, "atexit.c"),
            Object(NonMatching, "qsort.c"),
            Object(NonMatching, "sn_malloc.c"),
            Object(NonMatching, "allsrc.c"),
            Object(NonMatching, "audioplayer.cpp"),
            Object(NonMatching, "device_cmn.cpp"),
            Object(NonMatching, "rendercontext.cpp"),
            Object(NonMatching, "rendercontext_cmn.cpp"),
            Object(NonMatching, "state.cpp"),
            Object(NonMatching, "tar.cpp"),
            Object(NonMatching, "tevstage.cpp"),
            Object(NonMatching, "texturerc_cmn.cpp"),
            Object(NonMatching, "viewport.cpp"),
            Object(NonMatching, "viewport_cmn.cpp"),
            Object(NonMatching, "profiler_cmn.cpp"),
            Object(NonMatching, "singledraw.cpp"),
            Object(NonMatching, "base.cpp"),
            Object(NonMatching, "model.cpp"),
            Object(NonMatching, "rendermethod.cpp"),
            Object(NonMatching, "texturerc.cpp"),
            Object(NonMatching, "pcode.cpp"),
            Object(NonMatching, "locatbig.cpp"),
            Object(NonMatching, "filedev.cpp"),
            Object(NonMatching, "fixdmult.cpp"),
            Object(NonMatching, "gc_driver.cpp"),
            Object(NonMatching, "memvectors.cpp"),
            Object(NonMatching, "interfaceimp.cpp"),
            Object(NonMatching, "lib/cmn/locale.cpp"),
            Object(NonMatching, "inittmr.cpp"),
            Object(NonMatching, "initvblt.cpp"),
            Object(NonMatching, "mutex2.cpp"),
            Object(NonMatching, "printn3.cpp"),
            Object(NonMatching, "memcopy.cpp"),
            Object(NonMatching, "fontchar.cpp"),
            Object(NonMatching, "fontcreate.cpp"),
            Object(NonMatching, "fontdraw.cpp"),
            Object(NonMatching, "fontdrawf.cpp"),
            Object(NonMatching, "fontkern.cpp"),
            Object(NonMatching, "fontnull.cpp"),
            Object(NonMatching, "loccore.cpp"),
            Object(NonMatching, "ustrcpy.cpp"),
            Object(NonMatching, "creates.cpp"),
            Object(NonMatching, "shptype.cpp"),
            Object(NonMatching, "swizzlesize.cpp"),
            Object(NonMatching, "cluttype.cpp"),
            Object(NonMatching, "csis/dev/source/library/cmn/csis.cpp"),
            Object(NonMatching, "sk8/sk8memorycard/dev/source/dummy.c"),
            Object(NonMatching, "prodg_fixes.cpp"),
            Object(NonMatching, "codec/cmn/refsize.cpp"),
        ],
    },
    DolphinLib(
        "ar",
        [
            Object(NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/ar/ar.c"),
        ],
    ),
    DolphinLib(
        "arq",
        [
            Object(
                NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/arq/arq.c"
            ),
        ],
    ),
    DolphinLib(
        "ax",
        [
            Object(
                NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/ax/AXAlloc.c"
            ),
            Object(
                NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/ax/AXAux.c"
            ),
            Object(
                NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/ax/AXCL.c"
            ),
            Object(NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/ax/AX.c"),
            Object(
                NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/ax/AXOut.c"
            ),
            Object(
                NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/ax/AXSPB.c"
            ),
            Object(
                NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/ax/AXVPB.c"
            ),
            Object(
                NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/ax/AXProf.c"
            ),
        ],
    ),
    DolphinLib(
        "card",
        [
            Object(
                NonMatching,
                "Speed/GameCube/bWare/GameCube/dolphinsdk/src/card/CARDBios.c",
            ),
            Object(
                NonMatching,
                "Speed/GameCube/bWare/GameCube/dolphinsdk/src/card/CARDBlock.c",
            ),
            Object(
                NonMatching,
                "Speed/GameCube/bWare/GameCube/dolphinsdk/src/card/CARDDir.c",
            ),
            Object(
                NonMatching,
                "Speed/GameCube/bWare/GameCube/dolphinsdk/src/card/CARDCheck.c",
            ),
            Object(
                NonMatching,
                "Speed/GameCube/bWare/GameCube/dolphinsdk/src/card/CARDMount.c",
            ),
            Object(
                NonMatching,
                "Speed/GameCube/bWare/GameCube/dolphinsdk/src/card/CARDFormat.c",
            ),
            Object(
                NonMatching,
                "Speed/GameCube/bWare/GameCube/dolphinsdk/src/card/CARDCreate.c",
            ),
            Object(
                NonMatching,
                "Speed/GameCube/bWare/GameCube/dolphinsdk/src/card/CARDRead.c",
            ),
            Object(
                NonMatching,
                "Speed/GameCube/bWare/GameCube/dolphinsdk/src/card/CARDWrite.c",
            ),
            Object(
                NonMatching,
                "Speed/GameCube/bWare/GameCube/dolphinsdk/src/card/CARDDelete.c",
            ),
            Object(
                NonMatching,
                "Speed/GameCube/bWare/GameCube/dolphinsdk/src/card/CARDStat.c",
            ),
            Object(
                NonMatching,
                "Speed/GameCube/bWare/GameCube/dolphinsdk/src/card/CARDUnlock.c",
            ),
            Object(
                NonMatching,
                "Speed/GameCube/bWare/GameCube/dolphinsdk/src/card/CARDRdwr.c",
            ),
        ],
    ),
    DolphinLib(
        "dsp",
        [
            Object(
                NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/dsp/dsp.c"
            ),
            Object(
                NonMatching,
                "Speed/GameCube/bWare/GameCube/dolphinsdk/src/dsp/dsp_task.c",
            ),
        ],
    ),
    DolphinLib(
        "os",
        [
            Object(
                NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/os/OSFatal.c"
            ),
            Object(NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/os/OS.c"),
            Object(
                NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/os/OSAlarm.c"
            ),
            Object(
                NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/os/OSAlloc.c"
            ),
            Object(
                NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/os/OSArena.c"
            ),
            Object(
                NonMatching,
                "Speed/GameCube/bWare/GameCube/dolphinsdk/src/os/OSAudioSystem.c",
            ),
            Object(
                NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/os/OSCache.c"
            ),
            Object(
                NonMatching,
                "Speed/GameCube/bWare/GameCube/dolphinsdk/src/os/OSContext.c",
            ),
            Object(
                NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/os/OSError.c"
            ),
            Object(
                NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/os/OSFont.c"
            ),
            Object(
                NonMatching,
                "Speed/GameCube/bWare/GameCube/dolphinsdk/src/os/OSInterrupt.c",
            ),
            Object(
                NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/os/OSLink.c"
            ),
            Object(
                NonMatching,
                "Speed/GameCube/bWare/GameCube/dolphinsdk/src/os/OSMemory.c",
            ),
            Object(
                NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/os/OSReset.c"
            ),
            Object(
                NonMatching,
                "Speed/GameCube/bWare/GameCube/dolphinsdk/src/os/OSResetSW.c",
            ),
            Object(
                NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/os/OSRtc.c"
            ),
            Object(
                NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/os/OSSync.c"
            ),
            Object(
                NonMatching,
                "Speed/GameCube/bWare/GameCube/dolphinsdk/src/os/OSThread.c",
            ),
            Object(
                NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/os/OSTime.c"
            ),
            Object(
                NonMatching,
                "Speed/GameCube/bWare/GameCube/dolphinsdk/src/os/OSReboot.c",
            ),
            Object(
                NonMatching,
                "Speed/GameCube/bWare/GameCube/dolphinsdk/src/os/__ppc_eabi_init.cpp",
            ),
        ],
    ),
    DolphinLib(
        "db",
        [
            Object(NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/db/db.c"),
        ],
    ),
    DolphinLib(
        "mtx",
        [
            Object(
                NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/mtx/mtx.c"
            ),
            Object(
                NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/mtx/mtx44.c"
            ),
            Object(
                NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/mtx/vec.c"
            ),
        ],
    ),
    DolphinLib(
        "dvd",
        [
            Object(
                NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/dvd/dvdfs.c"
            ),
            Object(
                NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/dvd/dvd.c"
            ),
            Object(
                NonMatching,
                "Speed/GameCube/bWare/GameCube/dolphinsdk/src/dvd/dvdqueue.c",
            ),
            Object(
                NonMatching,
                "Speed/GameCube/bWare/GameCube/dolphinsdk/src/dvd/dvderror.c",
            ),
            Object(
                NonMatching,
                "Speed/GameCube/bWare/GameCube/dolphinsdk/src/dvd/dvdFatal.c",
            ),
            Object(
                NonMatching,
                "Speed/GameCube/bWare/GameCube/dolphinsdk/src/dvd/fstload.c",
            ),
            Object(
                NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/dvd/dvdlow.c"
            ),
        ],
    ),
    DolphinLib(
        "vi",
        [
            Object(NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/vi/vi.c"),
        ],
    ),
    DolphinLib(
        "pad",
        [
            Object(
                NonMatching,
                "Speed/GameCube/bWare/GameCube/dolphinsdk/src/pad/Padclamp.c",
            ),
            Object(
                NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/pad/Pad.c"
            ),
        ],
    ),
    DolphinLib(
        "ai",
        [
            Object(NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/ai/ai.c"),
        ],
    ),
    DolphinLib(
        "gx",
        [
            Object(
                NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/gx/GXInit.c"
            ),
            Object(
                NonMatching,
                "Speed/GameCube/bWare/GameCube/dolphinsdk/src/gx/GXFrameBuf.c",
            ),
            Object(
                NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/gx/GXAttr.c"
            ),
            Object(
                NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/gx/GXFifo.c"
            ),
            Object(
                NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/gx/GXMisc.c"
            ),
            Object(
                NonMatching,
                "Speed/GameCube/bWare/GameCube/dolphinsdk/src/gx/GXDisplayList.c",
            ),
            Object(
                NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/gx/GXLight.c"
            ),
            Object(
                NonMatching,
                "Speed/GameCube/bWare/GameCube/dolphinsdk/src/gx/GXTexture.c",
            ),
            Object(
                NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/gx/GXBump.c"
            ),
            Object(
                NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/gx/GXTev.c"
            ),
            Object(
                NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/gx/GXPixel.c"
            ),
            Object(
                NonMatching,
                "Speed/GameCube/bWare/GameCube/dolphinsdk/src/gx/GXTransform.c",
            ),
            Object(
                NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/gx/GXPerf.c"
            ),
        ],
    ),
    DolphinLib(
        "exi",
        [
            Object(
                NonMatching,
                "Speed/GameCube/bWare/GameCube/dolphinsdk/src/exi/EXIBios.c",
            ),
            Object(
                NonMatching,
                "Speed/GameCube/bWare/GameCube/dolphinsdk/src/exi/EXIUart.c",
            ),
        ],
    ),
    DolphinLib(
        "si",
        [
            Object(
                NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/si/SIBios.c"
            ),
            Object(
                NonMatching,
                "Speed/GameCube/bWare/GameCube/dolphinsdk/src/si/SISamplingRate.c",
            ),
            Object(
                NonMatching,
                "Speed/GameCube/bWare/GameCube/dolphinsdk/src/si/SISteering.c",
            ),
            Object(
                NonMatching,
                "Speed/GameCube/bWare/GameCube/dolphinsdk/src/si/SISteeringXfer.c",
            ),
            Object(
                NonMatching,
                "Speed/GameCube/bWare/GameCube/dolphinsdk/src/si/SISteeringAuto.c",
            ),
        ],
    ),
    DolphinLib(
        "ip",
        [
            Object(
                NonMatching,
                "Speed/GameCube/bWare/GameCube/dolphinsdk/src/ip/IPSocket.c",
            ),
            Object(
                NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/ip/IPPPPoE.c"
            ),
            Object(
                NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/ip/IPPap.c"
            ),
            Object(
                NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/ip/IPChap.c"
            ),
            Object(
                NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/ip/IPLcp.c"
            ),
            Object(NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/ip/IP.c"),
            Object(
                NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/ip/IPIcmp.c"
            ),
            Object(
                NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/ip/IPRoute.c"
            ),
            Object(
                NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/ip/IPFrag.c"
            ),
            Object(
                NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/ip/IPUdp.c"
            ),
            Object(
                NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/ip/IPEther.c"
            ),
            Object(
                NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/ip/IFFifo.c"
            ),
            Object(
                NonMatching,
                "Speed/GameCube/bWare/GameCube/dolphinsdk/src/ip/IPTcpTimeWait.c",
            ),
            Object(
                NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/ip/IPTcp.c"
            ),
            Object(
                NonMatching,
                "Speed/GameCube/bWare/GameCube/dolphinsdk/src/ip/IPTcpOutput.c",
            ),
            Object(
                NonMatching,
                "Speed/GameCube/bWare/GameCube/dolphinsdk/src/ip/IPTcpTimer.c",
            ),
            Object(
                NonMatching,
                "Speed/GameCube/bWare/GameCube/dolphinsdk/src/ip/IPTcpUser.c",
            ),
            Object(
                NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/ip/IPDns.c"
            ),
            Object(
                NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/ip/IPDhcp.c"
            ),
            Object(
                NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/ip/IPZero.c"
            ),
            Object(
                NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/ip/IPPPP.c"
            ),
            Object(
                NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/ip/IPArp.c"
            ),
        ],
    ),
    DolphinLib(
        "net",
        [
            Object(
                NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/net/eth.c"
            ),
            Object(
                NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/net/ethsec.c"
            ),
            Object(
                NonMatching, "Speed/GameCube/bWare/GameCube/dolphinsdk/src/net/md5.c"
            ),
        ],
    ),
    {
        "lib": "Runtime.PPCEABI.H",
        "toolchain_version": config.linker_version,
        "cflags": cflags_runtime,
        "progress_category": "sdk",  # str | List[str]
        "objects": [
            Object(NonMatching, "Runtime.PPCEABI.H/global_destructor_chain.c"),
            Object(NonMatching, "Runtime.PPCEABI.H/__init_cpp_exceptions.cpp"),
        ],
    },
    {
        "lib": "OdemuExi2",
        "toolchain_version": config.linker_version,
        "cflags": cflags_odemuexi,
        "progress_category": "sdk",  # str | List[str]
        "objects": [
            Object(
                NonMatching,
                "Speed/GameCube/bWare/GameCube/OdemuExi2/src/DebuggerDriver.c",
            ),
        ],
    },
    {
        "lib": "amcstubs",
        "mw_version": config.linker_version,
        "cflags": cflags_amcstub,
        "host": False,
        "progress_category": "sdk",  # str | List[str]
        "objects": [
            Object(
                NonMatching,
                "Speed/GameCube/bWare/GameCube/amcstubs/src/amcExi2/AmcExi.c",
            ),
            Object(
                NonMatching,
                "Speed/GameCube/bWare/GameCube/dolphinsdk/src/amcExi2/AmcExi2Comm.c",
            ),
        ],
    },
    {
        "lib": "libc",
        "toolchain_version": config.linker_version,
        "cflags": cflags_libc,
        "progress_category": "libc",  # str | List[str]
        "objects": [
            Object(NonMatching, "libc/vprintf.c"),
            Object(NonMatching, "libc/vsprintf.c"),
            Object(NonMatching, "libc/memcpy.c"),
            Object(NonMatching, "libc/memmove.c"),
            Object(NonMatching, "libc/memset.c"),
            Object(NonMatching, "libc/strcasecmp.c"),
            Object(NonMatching, "libc/strchr.c"),
            Object(NonMatching, "libc/strcmp.c"),
            Object(NonMatching, "libc/strcpy.c"),
            Object(NonMatching, "libc/strlen.c"),
            Object(NonMatching, "libc/strncmp.c"),
            Object(NonMatching, "libc/strncpy.c"),
            Object(NonMatching, "libc/vfprintf.c"),
            Object(NonMatching, "libc/impure.c"),
            Object(NonMatching, "libc/vfprintf_1.c"),
            Object(NonMatching, "libc/locale.c"),
            Object(NonMatching, "libc/_tolower.c"),
            Object(NonMatching, "libc/math_support.c"),
            Object(NonMatching, "libc/mbtowc_r.c"),
            Object(NonMatching, "libc/libgcc2.c"),
            Object(NonMatching, "libc/memchr.c"),
            Object(NonMatching, "libc/libgcc2_1.c"),
            Object(NonMatching, "libc/libgcc2_2.c"),
            Object(NonMatching, "libc/libgcc2_3.c"),
            Object(NonMatching, "libc/libgcc2_5.c"),
            Object(NonMatching, "libc/libgcc2_6.c"),
            Object(NonMatching, "libc/libgcc2_7.c"),
            Object(NonMatching, "libc/libgcc2_8.c"),
            Object(NonMatching, "libc/libgcc2_9.c"),
            Object(NonMatching, "libc/libgcc2_10.c"),
            Object(NonMatching, "libc/e_pow.c"),
            Object(NonMatching, "libc/e_sqrt.c"),
            Object(NonMatching, "libc/s_fabs.c"),
            Object(NonMatching, "libc/ef_pow.c"),
            Object(NonMatching, "libc/ef_sqrt.c"),
            Object(NonMatching, "libc/sf_cos.c"),
            Object(NonMatching, "libc/sf_fabs.c"),
            Object(NonMatching, "libc/sf_sin.c"),
            Object(NonMatching, "libc/s_scalbn.c"),
            Object(NonMatching, "libc/sf_scalbn.c"),
            Object(NonMatching, "libc/kf_cos.c"),
            Object(NonMatching, "libc/kf_sin.c"),
            Object(NonMatching, "libc/ef_rem_pio2.c"),
            Object(NonMatching, "libc/s_copysign.c"),
            Object(NonMatching, "libc/sf_copysign.c"),
            Object(NonMatching, "libc/kf_rem_pio2.c"),
            Object(NonMatching, "libc/sf_floor.c"),
            Object(NonMatching, "libc/e_acos.c"),
            Object(NonMatching, "libc/e_atan2.c"),
            Object(NonMatching, "libc/s_atan.c"),
            Object(NonMatching, "libc/ef_atan2.c"),
            Object(NonMatching, "libc/vfscanf.c"),
            Object(NonMatching, "libc/strtod2.c"),
            Object(NonMatching, "sn_buf.cpp"),
            Object(NonMatching, "libc/tolower.c"),
            Object(NonMatching, "libc/puts.c"),
            Object(NonMatching, "libc/atoi.c"),
            Object(NonMatching, "libc/bsearch.c"),
            Object(NonMatching, "libc/memcmp.c"),
            Object(NonMatching, "libc/strstr.c"),
            Object(NonMatching, "libc/strtol.c"),
            Object(NonMatching, "libc/fvwrite.c"),
            Object(NonMatching, "libc/wsetup.c"),
            Object(NonMatching, "libc/fflush.c"),
            Object(NonMatching, "libc/fopen.c"),
            Object(NonMatching, "libc/fwalk.c"),
            Object(NonMatching, "libc/makebuf.c"),
            Object(NonMatching, "libc/stdio.c"),
            Object(NonMatching, "libc/closer.c"),
            Object(NonMatching, "libc/fstatr.c"),
            Object(NonMatching, "libc/lseekr.c"),
            Object(NonMatching, "libc/readr.c"),
            Object(NonMatching, "libc/writer.c"),
            Object(NonMatching, "libc/s_sin.c"),
            Object(NonMatching, "libc/sf_atan.c"),
            Object(NonMatching, "libc/sf_tan.c"),
            Object(NonMatching, "libc/k_cos.c"),
            Object(NonMatching, "libc/k_sin.c"),
            Object(NonMatching, "libc/k_tan.c"),
            Object(NonMatching, "libc/e_rem_pio2.c"),
            Object(NonMatching, "libc/kf_tan.c"),
            Object(NonMatching, "libc/k_rem_pio2.c"),
            Object(NonMatching, "libc/s_floor.c"),
        ],
    },
]


# Optional callback to adjust link order. This can be used to add, remove, or reorder objects.
# This is called once per module, with the module ID and the current link order.
#
# For example, this adds "dummy.c" to the end of the DOL link order if configured with --non-matching.
# "dummy.c" *must* be configured as a Matching (or Equivalent) object in order to be linked.
def link_order_callback(module_id: int, objects: List[str]) -> List[str]:
    # Don't modify the link order for matching builds
    if not config.non_matching:
        return objects
    if module_id == 0:  # DOL
        return objects + ["dummy.c"]
    return objects


# Uncomment to enable the link order callback.
# config.link_order_callback = link_order_callback


# Optional extra categories for progress tracking
# Adjust as desired for your project
config.progress_categories = [
    ProgressCategory("game", "Game Code"),
    ProgressCategory("sdk", "SDK Code"),
    ProgressCategory("libc", "STD Code"),
    ProgressCategory("libs", "Library Code"),
]
config.progress_each_module = args.verbose

if args.mode == "configure":
    # Write build.ninja and objdiff.json
    generate_build(config)
elif args.mode == "progress":
    # Print progress information
    calculate_progress(config)
else:
    sys.exit("Unknown mode: " + args.mode)
