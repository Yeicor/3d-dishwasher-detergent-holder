import os

import cadquery as cq

# show_object = lambda *args, **kwargs: None

# ================== PARAMETERS ==================
# 3D printing basics
tol = 0.2  # Tolerance
wall_min = 0.4  # Minimum wall width
wall = wall_min * 3  # Recommended wall width
eps = 1e-5  # A small number

# Measurements of the rotating arm it will be attached to
rotating_arm_size = cq.Vector(47, 60, 15)

device_height = 40  # Total depth of the device to be attached to the rotating arm
device_max_volume = 40  # In milliliters (== cm^3)
device_volume_marks = [20, 30]  # In milliliters (== cm^3)

# ================== MODELLING ==================

# Dishwasher arm
dishwasher_arm = (
    cq.Workplane("XY")
    .box(rotating_arm_size.x + 2, rotating_arm_size.y, rotating_arm_size.z, centered=(True, True, False))
    .edges("(>X or <X) and |Z")
    .chamfer(rotating_arm_size.y / 2 - eps, 1)
    .edges("#Z and (not |X)")
    .fillet(3)
    .translate((0, 0, device_height - rotating_arm_size.z))
    .faces(">Z").circle(rotating_arm_size.x / 2 - 3).extrude(2)  # Top of the arm
    .edges("<<Z[2]").edges("<<X[2] and <<Y[2]").fillet(wall_min)  # Fillet the edges
)
debug(dishwasher_arm, "dishwasher-rotating-arm")

# Liquid area
# Compute the height of the base
base_area_cm = rotating_arm_size.x * (rotating_arm_size.y - wall * 2) / 100
base_height_cm = device_max_volume / base_area_cm
base_height = base_height_cm * 10
device_volume_marks_height = [h * base_height_cm / device_max_volume * 10 for h in device_volume_marks]
liquid_area = (  # Detergent holder
    cq.Workplane("XY")
    .box(rotating_arm_size.x, rotating_arm_size.y - wall * 2, base_height, centered=(True, True, False))
)
show_object(liquid_area, "liquid-area", {"color": (0.0, 0.0, 1.0), "alpha": 0.5})

# Detergent holder
connector_dimensions = cq.Vector(3 * wall, 1 * wall)
connector_limit_depth = cq.Vector(4 * wall, 6 * wall)
holder = (
    # Create a basic cup
    cq.Workplane("XY")
    .box(rotating_arm_size.x, rotating_arm_size.y - 2 * wall, base_height, centered=(True, True, False))
    .faces(">Z")
    .shell(wall, kind="intersection")
    # Add the 4 corner sticks for the connection to the rotating arm
    .faces(">Z")
    .workplane()
    .rect(rotating_arm_size.x + wall, rotating_arm_size.y - 2 * wall + wall, centered=True, forConstruction=True)
    .vertices()
    .rect(wall, wall, centered=True)
    .extrude(device_height - base_height + connector_dimensions.x / 2)
    # Add connection to the rotating arm
    .faces(">Z")
    .workplane()
    .rect(rotating_arm_size.x - connector_dimensions.y, rotating_arm_size.y - 2 * wall + wall,
          centered=True, forConstruction=True)
    .vertices()
    .rect(connector_dimensions.y, wall)
    .extrude(-connector_dimensions.x)
    # Chamfer the connection for easier insertion and printing
    .edges("|Y").edges("<<X[2] or >>X[2]").chamfer(connector_dimensions.y - eps, connector_dimensions.x / 2 - eps)
    # Add a bottom limit to the connection
    .faces(">Z")
    .workplane(offset=-rotating_arm_size.z - connector_dimensions.x / 2)
    .rect(rotating_arm_size.x - connector_limit_depth.x, rotating_arm_size.y - 2 * wall + wall,
          centered=True, forConstruction=True)
    .vertices()
    .rect(connector_limit_depth.x, wall)
    .extrude(-connector_limit_depth.y)
    # Chamfer the bottom for easier printing
    .edges("|Y").edges("<<X[3] or >>X[3]").edges("<Z").chamfer(
        connector_limit_depth.x - eps, connector_limit_depth.y - eps)
)

# Add the volume marks
for h in device_volume_marks_height:
    holder = (
        holder.faces(">>Z[1]")
        .workplane(offset=h, centerOption="CenterOfMass")
        .rect(rotating_arm_size.x, rotating_arm_size.y - 2 * wall, centered=True, forConstruction=True)
        .vertices()
        .rect(wall * 2 - eps, wall * 2 - eps)
        .extrude(-999, taper=30)
    )

cross_pattern_hole_size = 1 if os.getenv('final_build') else base_height / 2 - eps  # 1 mm is SLOW but needed
holder = (
    holder
    # "Final" filleting for nicer look
    .edges("|Z and ((>X or <X) and (>Y or <Y))").fillet(wall - eps)
    .edges("<Z").fillet(wall - eps)
    # Apply the cross-pattern to the cup to let pressurized water flow through but not the detergent
    # - On the bottom
    .faces("<Z")
    .workplane()
    .rarray(cross_pattern_hole_size * 2, cross_pattern_hole_size * 2,
            int(rotating_arm_size.x / (cross_pattern_hole_size * 2)),
            int((rotating_arm_size.y - wall * 2) / (cross_pattern_hole_size * 2)))
    .rect(cross_pattern_hole_size, cross_pattern_hole_size, centered=True)
    .cutBlind(-wall)
    # - On the left and right sides
    .faces("<X")
    .workplane()
    .transformed(offset=(0, base_height / 2 + wall))
    .rarray(cross_pattern_hole_size * 2, cross_pattern_hole_size * 2,
            int((rotating_arm_size.y - wall * 2) / (cross_pattern_hole_size * 2)),
            int(base_height / (cross_pattern_hole_size * 2)))
    .rect(cross_pattern_hole_size, cross_pattern_hole_size, centered=True)
    .cutThruAll()
    # - On the front and back sides
    .faces("<Y")
    .workplane()
    .transformed(offset=(rotating_arm_size.x / 2 + wall, 0))
    .rarray(cross_pattern_hole_size * 2, cross_pattern_hole_size * 2,
            int(rotating_arm_size.x / (cross_pattern_hole_size * 2)),
            int(base_height / (cross_pattern_hole_size * 2)))
    .rect(cross_pattern_hole_size, cross_pattern_hole_size, centered=True)
    .cutThruAll()
)

show_object(holder, "detergent-holder")

# cq.exporters.export(holder, "detergent-holder.stl")
