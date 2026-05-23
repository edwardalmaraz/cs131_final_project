import json
import math
import matplotlib.pyplot as plt


def draw_pose(pose_name: str, json_file: str = "songs/metadata.json", ax=None, scale: float = 0.003):
   """
   Draws a stick figure for a named pose from your song JSON file.


   Args:
       pose_name:  e.g. "tpose", "both_arms_down", "star"
       json_file:  path to your song JSON file
       ax:         matplotlib Axes to draw on (creates new figure if None)
       scale:      shrinks raw pixel magnitudes to figure units
   Returns:
       fig, ax
   """
   # --- load and find the pose ---
   with open(json_file, "r") as f:
       data = json.load(f)


   pose_keypoints = None
   for pose in data["poses"]:
       if pose["pose_name"] == pose_name:
           pose_keypoints = pose["keypoints"]
           break


   if pose_keypoints is None:
       raise ValueError(f"Pose '{pose_name}' not found in {json_file}. "
                        f"Available: {[p['pose_name'] for p in data['poses']]}")


   # --- convert keypoint vectors to (x, y) ---
   def to_xy(kp):
       rad = kp["angle_rad"]
       mag = kp["magnitude"]
       return (math.cos(rad) * mag * scale,
               -math.sin(rad) * mag * scale)


   coords = {name: to_xy(kp) for name, kp in pose_keypoints.items()}


   CONNECTIONS = [
       ("left_shoulder",  "right_shoulder"),
       ("left_shoulder",  "left_elbow"),
       ("left_elbow",     "left_wrist"),
       ("right_shoulder", "right_elbow"),
       ("right_elbow",    "right_wrist"),
       ("left_shoulder",  "left_hip"),
       ("right_shoulder", "right_hip"),
       ("left_hip",       "right_hip"),
       ("left_hip",       "left_knee"),
       ("left_knee",      "left_ankle"),
       ("right_hip",      "right_knee"),
       ("right_knee",     "right_ankle"),
   ]


   HEAD_KPS = {"nose", "left_eye", "right_eye", "left_ear", "right_ear"}


   if ax is None:
       fig, ax = plt.subplots(figsize=(4, 6))
   else:
       fig = ax.get_figure()


   # draw limbs
   for a, b in CONNECTIONS:
       if a in coords and b in coords:
           ax.plot([coords[a][0], coords[b][0]],
                   [coords[a][1], coords[b][1]],
                   color="#3B8BD4", linewidth=3, solid_capstyle="round")


   # draw head circle (centered between ears)
   if "left_ear" in coords and "right_ear" in coords:
       lx, ly = coords["left_ear"]
       rx, ry = coords["right_ear"]
       hx = (lx + rx) / 2
       hy = (ly + ry) / 2
       r = math.sqrt((lx - rx)**2 + (ly - ry)**2) / 1.6
       head = plt.Circle((hx, hy), r, color="#E6F1FB", ec="#3B8BD4", linewidth=2, zorder=3)
       ax.add_patch(head)


   # draw joints
   for name, (x, y) in coords.items():
       if name in HEAD_KPS:
           continue
       ax.plot(x, y, "o", color="#E6F1FB", markeredgecolor="#185FA5",
               markersize=8, markeredgewidth=2, zorder=4)


   ax.set_aspect("equal")
   ax.axis("off")
   ax.invert_yaxis()
   ax.set_title(pose_name.replace("_", " "), fontsize=11)


   return fig, ax




def draw_all_poses(json_file: str = "song_example.json"):
   """Draws every pose defined in the JSON file as a grid."""
   with open(json_file, "r") as f:
       data = json.load(f)


   pose_names = [p["pose_name"] for p in data["poses"]]
   cols = 3
   rows = math.ceil(len(pose_names) / cols)
   fig, axes = plt.subplots(rows, cols, figsize=(4 * cols, 6 * rows))
   axes = axes.flatten()


   for i, name in enumerate(pose_names):
       draw_pose(name, json_file=json_file, ax=axes[i])


   for j in range(len(pose_names), len(axes)):
       axes[j].axis("off")


   fig.tight_layout()
   return fig
