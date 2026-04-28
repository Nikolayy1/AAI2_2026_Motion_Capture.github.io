# OpenSim Integration Guide

This guide explains how to integrate OpenSim analysis results with the web frontend.

## Backend API Endpoints

Your backend should provide these endpoints:

### GET `/opensim/model`
Returns the 3D musculoskeletal model data for visualization.

**Response Format:**
```json
{
  "bones": [
    {
      "name": "femur_r",
      "length": 0.4,
      "position": {"x": 0.1, "y": -0.2, "z": 0},
      "rotation": {"x": 0, "y": 0, "z": 0.1}
    },
    {
      "name": "tibia_r",
      "length": 0.35,
      "position": {"x": 0.1, "y": -0.55, "z": 0},
      "rotation": {"x": 0, "y": 0, "z": 0.05}
    }
  ],
  "joints": [
    {
      "name": "knee_r",
      "position": {"x": 0.1, "y": -0.4, "z": 0},
      "type": "hinge"
    },
    {
      "name": "ankle_r",
      "position": {"x": 0.1, "y": -0.7, "z": 0},
      "type": "hinge"
    }
  ],
  "muscles": [
    {
      "name": "quadriceps_r",
      "points": [
        {"x": 0.05, "y": -0.1, "z": 0.05},
        {"x": 0.08, "y": -0.3, "z": 0.03},
        {"x": 0.1, "y": -0.45, "z": 0}
      ],
      "activated": true,
      "activation": 0.75
    },
    {
      "name": "hamstrings_r",
      "points": [
        {"x": 0.15, "y": -0.1, "z": -0.05},
        {"x": 0.12, "y": -0.3, "z": -0.03},
        {"x": 0.1, "y": -0.45, "z": 0}
      ],
      "activated": false,
      "activation": 0.2
    }
  ]
}
```

### GET `/opensim/analysis`
Returns the biomechanical analysis results.

**Response Format:**
```json
{
  "jointForces": {
    "knee_r": 1250.5,
    "ankle_r": 890.3,
    "hip_r": 2100.8
  },
  "muscleActivations": {
    "quadriceps_r": 0.85,
    "hamstrings_r": 0.25,
    "glutes_r": 0.65,
    "calves_r": 0.45
  },
  "kinematics": {
    "jointAngles": {
      "knee_flexion": 25.3,
      "ankle_dorsiflexion": 15.7
    },
    "groundReactionForce": {
      "x": 150.2,
      "y": -890.5,
      "z": 45.8
    }
  },
  "metadata": {
    "analysisType": "inverse_dynamics",
    "modelVersion": "gait2392",
    "processingTime": "2.3s"
  }
}
```

### GET `/opensim/animation`
Returns a simplified animation sequence for the frontend viewer.

**Response Format:**
```json
{
  "frames": [
    {
      "bones": [ ... ],
      "joints": [ ... ],
      "muscles": [ ... ]
    }
  ],
  "fps": 24
}
```

The viewer expects an array of frames with bone/joint/muscle positions and rotations.

## Python Backend Example

Here's how to structure your OpenSim processing in Python:

```python
import opensim as osim
import numpy as np
from fastapi import FastAPI

app = FastAPI()

def process_opensim_analysis(motion_data):
    # Load model
    model = osim.Model('gait2392.osim')

    # Set up analysis tools
    ik_tool = osim.InverseKinematicsTool()
    ik_tool.setModel(model)
    ik_tool.setMarkerDataFile(motion_data)
    ik_tool.run()

    # Run inverse dynamics
    id_tool = osim.InverseDynamicsTool()
    id_tool.setModel(model)
    id_tool.run()

    # Extract results
    return extract_analysis_results(model)

@app.get("/opensim/model")
def get_opensim_model():
    # Return simplified model data for 3D visualization
    return {
        "bones": [...],  # Extract from OpenSim model
        "joints": [...],
        "muscles": [...]
    }

@app.get("/opensim/analysis")
def get_analysis_results():
    # Return latest analysis results
    return {
        "jointForces": {...},
        "muscleActivations": {...},
        "kinematics": {...}
    }
```

## Data Processing Pipeline

1. **Motion Capture** → Extract joint positions from video
2. **OpenSim IK** → Compute joint angles from marker data
3. **Inverse Dynamics** → Calculate joint forces and moments
4. **Muscle Analysis** → Determine muscle activations
5. **Visualization** → Send simplified data to frontend

## Frontend Integration

The frontend automatically loads OpenSim data when the view page is accessed. The 3D viewer displays:
- Skeletal structure (bones as cylinders)
- Joint locations (spheres)
- Muscle paths (colored tubes based on activation)
- Analysis results in a side panel

## Model Simplification

Since full OpenSim models are complex XML files, the backend should provide simplified geometric representations suitable for web-based 3D rendering.