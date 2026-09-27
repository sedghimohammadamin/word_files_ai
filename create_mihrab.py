#!/usr/bin/env python3
"""Build a texture-ready, modular Persian tiled gateway from the supplied photo.

No third-party libraries required:
    python3 create_mihrab.py

Output: mihrab_qom.obj + mihrab_qom.mtl. Every brick and tile is its own object,
with a local 0-1 UV island. Model axes: X width, Y depth, Z up; front faces -Y.
"""
from pathlib import Path
import math

OUT = Path(__file__).resolve().parent
OBJ, MTL = OUT / "mihrab_qom.obj", OUT / "mihrab_qom.mtl"
parts = []
materials = {
    "Brick_Sandstone": ((0.59,0.34,0.19),0.0),
    "Brick_Buff": ((0.70,0.45,0.27),0.0),
    "Brick_Honey": ((0.77,0.53,0.32),0.0),
    "Brick_Shadow": ((0.43,0.25,0.15),0.0),
    "Mortar_Lime": ((0.57,0.49,0.39),0.0),
    "Tile_Cobalt_Glaze": ((0.025,0.075,0.32),0.9),
    "Tile_Deep_Blue_Glaze": ((0.018,0.045,0.19),0.9),
    "Tile_Lapis_Glaze": ((0.07,0.20,0.61),0.9),
    "Tile_Turquoise_Glaze": ((0.015,0.39,0.43),0.9),
    "Tile_Teal_Glaze": ((0.012,0.22,0.25),0.9),
    "Tile_Ivory_Glaze": ((0.84,0.72,0.53),0.83),
    "Tile_Gold_Glaze": ((0.78,0.43,0.10),0.82),
    "Foliage_Evergreen": ((0.055,0.19,0.085),0.08),
    "Wood_Dark": ((0.25,0.12,0.065),0.0),
    "Stone_Carved": ((0.62,0.56,0.45),0.0),
    "Structure_Core": ((0.48,0.39,0.29),0.0),
}


def add(name, mat, verts, faces):
    parts.append((name,mat,verts,faces))


def chamfer_rect(x0,x1,z0,z1,c=0.008):
    c=max(0.0,min(c,(x1-x0)*0.20,(z1-z0)*0.20))
    if c < 1e-6: return [(x0,z0),(x1,z0),(x1,z1),(x0,z1)]
    return [(x0+c,z0),(x1-c,z0),(x1,z0+c),(x1,z1-c),
            (x1-c,z1),(x0+c,z1),(x0,z1-c),(x0,z0+c)]


def prism(name,mat,poly,y_front,y_back):
    """Solid X/Z polygon, with front face toward -Y."""
    n=len(poly)
    verts=[(x,y_front,z) for x,z in poly]+[(x,y_back,z) for x,z in poly]
    faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]
    for i in range(n):
        j=(i+1)%n
        faces.append((i,j,n+j,n+i))
    add(name,mat,verts,faces)


def block(name,mat,x,z,w,h,yfront,depth,bevel=0.008):
    prism(name,mat,chamfer_rect(x-w/2,x+w/2,z-h/2,z+h/2,bevel),yfront,yfront+depth)


def surface(name,mat,verts):
    add(name,mat,verts,[tuple(range(len(verts)))])


# Architectural proportions from the reference: broad open passage, deep
# two-sided brick piers, a shallow pointed crown and a generously tiled archivolt.
OPEN_W=3.72
SHOULDER=6.70
OPEN_APEX=9.55
OUTER_W=6.70
TOP=10.58
Y_FRONT=-2.00
Y_BACK=0.82
DEPTH=Y_BACK-Y_FRONT


def arch_z(width,t):
    apex=OPEN_APEX+0.20*(width-OPEN_W)
    return SHOULDER+(apex-SHOULDER)*(1.0-(1.0-t)**1.52)


def arch_point(width,side,t):
    return (side*width*(1.0-t),arch_z(width,t))


def x_at_height(width,z):
    apex=OPEN_APEX+0.20*(width-OPEN_W)
    if z<=SHOULDER: return width
    if z>=apex: return 0.0
    q=1.0-(z-SHOULDER)/(apex-SHOULDER)
    return width*(q**(1.0/1.52))


def ring_segment(name,mat,wi,wo,side,t0,t1,yfront,depth):
    # One independent masonry voussoir or glazed tile in an arch ring.
    poly=[arch_point(wo,side,t0),arch_point(wo,side,t1),
          arch_point(wi,side,t1),arch_point(wi,side,t0)]
    prism(name,mat,poly,yfront,yfront+depth)


def face_quad(name,mat,verts):
    surface(name,mat,verts)


# STRUCTURAL BODY: two massive piers and spandrels, leaving a true through-opening.
# The solids stop exactly at the inner arch curve; no niche/back panel is present.
for side,label in [(-1,"L"),(1,"R")]:
    block(f"CORE_{label}_Monumental_Pier","Structure_Core",
          side*(OPEN_W+OUTER_W)/2,TOP/2,OUTER_W-OPEN_W,TOP,Y_FRONT,DEPTH,0.0)
    pts=[(side*OPEN_W,SHOULDER)]
    pts += [arch_point(OPEN_W,side,i/40) for i in range(1,41)]
    pts += [(side*OPEN_W,OPEN_APEX)]
    prism(f"CORE_{label}_Arch_Spandrel","Structure_Core",pts,Y_FRONT,Y_BACK)
# Head/header masonry closes the small crown above the clear arch and joins the piers.
block("CORE_Crown_Header","Structure_Core",0,(OPEN_APEX+TOP)/2,
      2*OUTER_W,TOP-OPEN_APEX,Y_FRONT,DEPTH,0.0)

# PLINTHS and a through-threshold, as seen in the reference gateway.
for side,label in [(-1,"L"),(1,"R")]:
    block(f"PLINTH_{label}_Lower_Stone","Stone_Carved",side*5.15,0.16,3.10,0.32,-2.12,3.06,0.025)
    block(f"PLINTH_{label}_Upper_Band","Tile_Cobalt_Glaze",side*5.15,0.365,3.00,0.075,-2.17,3.12,0.008)
block("THRESHOLD_Stone_Sill","Stone_Carved",0,0.075,7.48,0.15,-2.04,2.94,0.012)

# FRONT FACE BRICK CLADDING over the piers: individual running-bond units with
# real mortar gaps, warm sandstone tones, and mild hand-laid variation.
brick_w,brick_h,gap_x,gap_z=0.365,0.185,0.024,0.025
pitch_x,pitch_z=brick_w+gap_x,brick_h+gap_z
brick_mats=["Brick_Sandstone","Brick_Buff","Brick_Honey","Brick_Shadow"]
for side,label in [(-1,"L"),(1,"R")]:
    row=0
    z=0.47
    while z<TOP-0.1:
        offset=(row%2)*pitch_x/2
        col=0
        x=OPEN_W+0.10+offset
        while x<OUTER_W-0.05:
            cx=x+brick_w/2
            # Outer voussoir courses take over this part of the facade above the spring.
            skip=False
            if SHOULDER-0.18 < z < OPEN_APEX+0.20*(6.38-OPEN_W):
                inner_edge=x_at_height(OPEN_W,z)
                outer_edge=x_at_height(6.38,z)
                if inner_edge-0.20 < cx < outer_edge+0.20: skip=True
            if not skip:
                jitter=((row*13+col*7)%5-2)*0.002
                mat=brick_mats[(row*3+col*5+row//4)%len(brick_mats)]
                block(f"FACADE_BRICK_{label}_R{row+1:02d}_C{col+1:02d}",mat,
                      side*(cx+jitter),z+((row+col)%3-1)*0.001,
                      brick_w,brick_h,-2.135,0.125,0.009)
            x+=pitch_x
            col+=1
        z+=pitch_z
        row+=1

# Outer side faces of the thick piers are also fully coursed in brick.
for side,label in [(-1,"L"),(1,"R")]:
    row=0
    z=0.36
    while z<TOP-0.1:
        col=0
        y=Y_FRONT+0.16+(row%2)*0.17
        while y<Y_BACK-0.10:
            mat=brick_mats[(row+col*3+2)%len(brick_mats)]
            y0=y
            # Extruded brick boxes rotated onto the outer X-facing elevation.
            x0,x1=(side*OUTER_W,side*(OUTER_W-0.125)) if side>0 else (side*(OUTER_W-0.125),side*OUTER_W)
            z0,z1=z-brick_h/2,z+brick_h/2
            verts=[(x0,y0,z0),(x0,y0+0.32,z0),(x0,y0+0.32,z1),(x0,y0,z1),
                   (x1,y0,z0),(x1,y0+0.32,z0),(x1,y0+0.32,z1),(x1,y0,z1)]
            faces=[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]
            add(f"OUTER_SIDE_BRICK_{label}_R{row+1:02d}_C{col+1:02d}",mat,verts,faces)
            y+=0.36
            col+=1
        z+=pitch_z
        row+=1

# MOSAIC FIELD on the broad front spandrels and upper tympanum. Every tessera is
# an individual shallow beveled tile; motifs are actual relief meshes, not images.
TILE=0.188
TILE_GAP=0.014
TILE_PITCH=TILE+TILE_GAP
FIELD_Y=-2.205

def in_mosaic_field(x,z,margin=0.0):
    ax=abs(x)
    # side panels from the inside archivolt out toward the brick piers
    if z < SHOULDER-0.20:
        return OPEN_W+0.22+margin < ax < 5.24-margin and z>0.50
    # upper tympanum lies above the open arch and inside the tiled spandrel field
    if z < OPEN_APEX+margin:
        inner=x_at_height(OPEN_W,z)
        return inner+0.14+margin < ax < 5.24-margin
    return ax < 5.24-margin and z<TOP-0.06


def point_material(gx,gz,x,z):
    # Persian star-and-cross repeat in glazed cobalt, turquoise, ivory and gold.
    sx=round((x+4.75)/1.12)
    sz=round((z-6.15)/1.12)
    dd=math.hypot(x-(-4.75+sx*1.12),z-(6.15+sz*1.12))
    if dd<0.13: return "Tile_Ivory_Glaze"
    if dd<0.34:
        return "Tile_Gold_Glaze" if (sx+sz)%2==0 else "Tile_Turquoise_Glaze"
    pat=(gx*7+gz*11+(gx//5)*3+(gz//5)*5)%23
    if pat in (0,1,7): return "Tile_Turquoise_Glaze"
    if pat in (3,13): return "Tile_Ivory_Glaze"
    if pat in (5,17): return "Tile_Lapis_Glaze"
    if pat==19: return "Tile_Teal_Glaze"
    return "Tile_Cobalt_Glaze"

# Use a global grid, so all tile joints are straight and properly aligned.
grid_i=0
x=-5.25
while x<5.25:
    z=0.47
    grid_j=0
    while z<TOP-0.06:
        cx=x+TILE/2; cz=z+TILE/2
        if in_mosaic_field(cx,cz):
            mat=point_material(grid_i,grid_j,cx,cz)
            block(f"FACADE_MOSAIC_X{grid_i+1:02d}_Z{grid_j+1:02d}",mat,
                  cx,cz,TILE,TILE,FIELD_Y,0.055,0.009)
        z+=TILE_PITCH
        grid_j+=1
    x+=TILE_PITCH
    grid_i+=1

# Eight-point star rosettes in relief over the tesserae. The clear surround
# guarantees no motif intrudes into the open arch or crosses the arch ring.
for col in range(-4,5):
    for row in range(0,5):
        cx=col*1.12
        cz=6.15+row*1.12
        if not in_mosaic_field(cx,cz,margin=0.39): continue
        pts=[]
        for i in range(16):
            a=math.pi/8+i*math.pi/8
            r=0.36 if i%2==0 else 0.20
            pts.append((cx+r*math.cos(a),cz+r*math.sin(a)))
        prism(f"MOSAIC_Rosette_{col+5:02d}_{row+1:02d}",
              "Tile_Gold_Glaze" if (col+row)%2==0 else "Tile_Ivory_Glaze",
              pts,-2.275,-2.245)
        # small blue centre star is a separate glazed element
        center=[]
        for i in range(8):
            a=math.pi/4+i*math.pi/4
            r=0.105 if i%2==0 else 0.060
            center.append((cx+r*math.cos(a),cz+r*math.sin(a)))
        prism(f"MOSAIC_Rosette_Centre_{col+5:02d}_{row+1:02d}",
              "Tile_Cobalt_Glaze",center,-2.292,-2.275)

# ARCHIVOLT: six bands of blue/turquoise/ivory glazed tesserae, followed by four
# radial courses of voussoir bricks. Keystones meet cleanly at the pointed crown.
ring_specs=[
    (3.72,3.94,"Tile_Turquoise_Glaze",0.12),
    (3.95,4.18,"Tile_Cobalt_Glaze",0.13),
    (4.19,4.42,"Tile_Ivory_Glaze",0.14),
    (4.43,4.67,"Tile_Turquoise_Glaze",0.15),
    (4.68,4.93,"Tile_Deep_Blue_Glaze",0.16),
    (4.94,5.20,"Tile_Lapis_Glaze",0.17),
    (5.21,5.48,"Brick_Honey",0.19),
    (5.49,5.77,"Brick_Buff",0.20),
    (5.78,6.06,"Brick_Sandstone",0.21),
    (6.07,6.36,"Brick_Honey",0.22),
]
ARCH_SEGMENTS=30
for ring,(wi,wo,base,depth) in enumerate(ring_specs):
    for side,label in [(-1,"L"),(1,"R")]:
        for s in range(ARCH_SEGMENTS):
            t0=s/ARCH_SEGMENTS+0.002
            t1=(s+1)/ARCH_SEGMENTS-0.002
            mat=base
            if base=="Tile_Cobalt_Glaze" and s%7==2: mat="Tile_Lapis_Glaze"
            if base=="Tile_Turquoise_Glaze" and s%8==3: mat="Tile_Teal_Glaze"
            ring_segment(f"ARCH_RING_{ring+1:02d}_{label}_VOUSSOIR_{s+1:02d}",
                         mat,wi,wo,side,t0,t1,-2.285,depth)

# VERTICAL ARCH/JAMB STRIPS, built as separate upright ceramic and brick blocks.
# The narrow colored reveal strip turns the arch decoration down the piers.
for side,label in [(-1,"L"),(1,"R")]:
    for band,(inner,outer,mat) in enumerate([
        (3.72,3.94,"Tile_Turquoise_Glaze"),(3.95,4.18,"Tile_Cobalt_Glaze"),
        (4.19,4.42,"Tile_Ivory_Glaze"),(4.43,4.67,"Tile_Turquoise_Glaze"),
        (4.68,4.93,"Tile_Deep_Blue_Glaze"),(4.94,5.20,"Tile_Lapis_Glaze"),
        (5.21,5.48,"Brick_Honey"),(5.49,5.77,"Brick_Buff"),
        (5.78,6.06,"Brick_Sandstone"),(6.07,6.36,"Brick_Honey")]):
        for k in range(32):
            z0=0.20+k*0.205+0.009
            z1=min(z0+0.187,SHOULDER-0.02)
            if z1<=z0: continue
            block(f"JAMB_RING_{band+1:02d}_{label}_UNIT_{k+1:02d}",mat,
                  side*(inner+outer)/2,(z0+z1)/2,outer-inner,z1-z0,
                  -2.285,0.18,0.008)

# OPEN PASSAGE: real tiled vault soffit (underside of the arch) carried deep into
# the portal. Separate small curved modules follow both halves of the arch.
VAULT_ROWS=48
DEPTH_ROWS=14
for side,label in [(-1,"L"),(1,"R")]:
    for s in range(VAULT_ROWS):
        t0=s/VAULT_ROWS+0.001
        t1=(s+1)/VAULT_ROWS-0.001
        p0=arch_point(OPEN_W,side,t0); p1=arch_point(OPEN_W,side,t1)
        for d in range(DEPTH_ROWS):
            y0=Y_FRONT+d*DEPTH/DEPTH_ROWS+0.008
            y1=Y_FRONT+(d+1)*DEPTH/DEPTH_ROWS-0.008
            mat=("Tile_Cobalt_Glaze" if (s+d)%7 not in (1,4) else
                 "Tile_Turquoise_Glaze" if (s+d)%7==1 else "Tile_Ivory_Glaze")
            face_quad(f"VAULT_SOFFIT_{label}_T{s+1:02d}_D{d+1:02d}",mat,
                      [(p0[0],y0,p0[1]),(p1[0],y0,p1[1]),
                       (p1[0],y1,p1[1]),(p0[0],y1,p0[1])])

# Passage cheek walls: individually laid brick courses on the two inner vertical
# returns. They reveal the full thickness of the gateway; the center stays open.
for side,label in [(-1,"L"),(1,"R")]:
    row=0; z=0.14
    while z<SHOULDER-0.08:
        y=Y_FRONT+0.05+(row%2)*0.18
        col=0
        while y<Y_BACK-0.30:
            y0=y; y1=y+0.335
            z0=z; z1=z+0.17
            # thin brick volume on the inward-facing plane
            if side<0: xa,xb=-OPEN_W-0.13,-OPEN_W
            else: xa,xb=OPEN_W,OPEN_W+0.13
            verts=[(xa,y0,z0),(xa,y1,z0),(xa,y1,z1),(xa,y0,z1),
                   (xb,y0,z0),(xb,y1,z0),(xb,y1,z1),(xb,y0,z1)]
            faces=[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]
            mat=brick_mats[(row+col*3+1)%len(brick_mats)]
            add(f"PASSAGE_CHEEK_BRICK_{label}_R{row+1:02d}_C{col+1:02d}",mat,verts,faces)
            y+=0.36; col+=1
        z+=pitch_z; row+=1

# Stone corner blocks and carved cap courses emphasize the monumental scale.
for side,label in [(-1,"L"),(1,"R")]:
    for course,(z,h,mat) in enumerate([(0.16,0.32,"Stone_Carved"),
                                        (0.42,0.12,"Brick_Shadow"),
                                        (0.60,0.08,"Tile_Cobalt_Glaze")]):
        block(f"BASE_MOULDING_{label}_{course+1}",mat,side*5.12,z,3.05,h,-2.22,3.20,0.018)
block("CROWN_Front_Cornice","Stone_Carved",0,10.43,13.42,0.30,-2.14,3.00,0.025)


# ---------------------------------------------------------------------------
# COURTYARD / SHRINE VISIBLE THROUGH THE OPEN GATE
# The reference is a complete view into a mosque courtyard, not an isolated
# arch. Add the distant tiled sanctuary, flanking riwaq arcades, paving, trees,
# and courtyard lanterns as separate low-level architectural geometry.
# ---------------------------------------------------------------------------

# A module helper for faceted cylinder surface tiles, each selectable/UV mapped.
def cylinder_panel(name,mat,cx,cy,r,z0,z1,a0,a1):
    verts=[(cx+r*math.cos(a0),cy+r*math.sin(a0),z0),
           (cx+r*math.cos(a1),cy+r*math.sin(a1),z0),
           (cx+r*math.cos(a1),cy+r*math.sin(a1),z1),
           (cx+r*math.cos(a0),cy+r*math.sin(a0),z1)]
    face_quad(name,mat,verts)


def rect_slab(name,mat,cx,cy,z0,width,depth,height):
    x0,x1=cx-width/2,cx+width/2
    y0,y1=cy-depth/2,cy+depth/2
    verts=[(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),
           (x0,y0,z0+height),(x1,y0,z0+height),(x1,y1,z0+height),(x0,y1,z0+height)]
    faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    add(name,mat,verts,faces)


def horizontal_slab(name,mat,cx,cy,z0,width,depth,height,sides=12):
    ring=[(cx+width/2*math.cos(2*math.pi*i/sides),
           cy+depth/2*math.sin(2*math.pi*i/sides)) for i in range(sides)]
    n=len(ring)
    verts=[(x,y,z0) for x,y in ring]+[(x,y,z0+height) for x,y in ring]
    faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]
    for i in range(n):
        j=(i+1)%n
        faces.append((i,j,n+j,n+i))
    add(name,mat,verts,faces)


def custom_arch_point(width,side,t,shoulder,apex,exponent=1.48):
    return (side*width*(1-t),shoulder+(apex-shoulder)*(1-(1-t)**exponent))


def custom_arch_polygon(width,shoulder,apex):
    pts=[(-width,0),(width,0),(width,shoulder)]
    pts += [custom_arch_point(width,1,i/32,shoulder,apex) for i in range(1,33)]
    pts += [custom_arch_point(width,-1,i/32,shoulder,apex) for i in range(32,-1,-1)]
    pts += [(-width,shoulder)]
    return pts

# Grand mosque/shrine centered behind the gateway. Its broad blue tiled facade
# is scaled to sit naturally inside the portal opening.
SHRINE_Y=15.15
SHRINE_FRONT=14.55
SHRINE_HALF=2.62
SHRINE_EAVE=4.28
DOOR_W=1.08
DOOR_SHOULDER=2.55
DOOR_APEX=3.60
for side,label in [(-1,"L"),(1,"R")]:
    block(f"SHRINE_FACADE_{label}_WING","Structure_Core",
          side*(DOOR_W+SHRINE_HALF)/2,SHRINE_EAVE/2,
          SHRINE_HALF-DOOR_W,SHRINE_EAVE,SHRINE_FRONT,0.78,0.0)
block("SHRINE_FACADE_CROWN","Structure_Core",0,(DOOR_APEX+SHRINE_EAVE)/2,
      2*SHRINE_HALF,SHRINE_EAVE-DOOR_APEX,SHRINE_FRONT,0.78,0.0)
# Shadowed pointed entrance leaf at the back of a shallow iwan.
prism("SHRINE_PORTAL_DARK_RECESS","Tile_Deep_Blue_Glaze",
      custom_arch_polygon(DOOR_W,DOOR_SHOULDER,DOOR_APEX),14.18,14.28)
# Small concentric ceramic archivolt around the shrine entrance.
for band,(wi,wo,mat) in enumerate([
    (1.08,1.18,"Tile_Ivory_Glaze"),(1.19,1.31,"Tile_Gold_Glaze"),
    (1.32,1.44,"Tile_Turquoise_Glaze"),(1.45,1.58,"Tile_Cobalt_Glaze")]):
    for side,label in [(-1,"L"),(1,"R")]:
        for s in range(18):
            t0=s/18+0.003;t1=(s+1)/18-0.003
            poly=[custom_arch_point(wo,side,t0,DOOR_SHOULDER,DOOR_APEX),
                  custom_arch_point(wo,side,t1,DOOR_SHOULDER,DOOR_APEX),
                  custom_arch_point(wi,side,t1,DOOR_SHOULDER,DOOR_APEX),
                  custom_arch_point(wi,side,t0,DOOR_SHOULDER,DOOR_APEX)]
            prism(f"SHRINE_DOOR_ARCH_{band+1}_{label}_{s+1:02d}",mat,poly,14.42,14.56)
# Vertical jamb continuations for the shrine door frame.
for side,label in [(-1,"L"),(1,"R")]:
    for band,(wi,wo,mat) in enumerate([
        (1.08,1.18,"Tile_Ivory_Glaze"),(1.19,1.31,"Tile_Gold_Glaze"),
        (1.32,1.44,"Tile_Turquoise_Glaze"),(1.45,1.58,"Tile_Cobalt_Glaze")]):
        for row in range(11):
            z0=0.08+row*0.22;z1=z0+0.19
            block(f"SHRINE_DOOR_JAMB_{band+1}_{label}_{row+1:02d}",mat,
                  side*(wi+wo)/2,(z0+z1)/2,wo-wi,z1-z0,14.42,0.14,0.006)
# Faience tesserae on the sanctuary's side panels and upper tympanum.
small=0.155; smallgap=0.012; smallpitch=small+smallgap
for ix in range(-17,18):
    for iz in range(0,27):
        cx=ix*smallpitch;cz=0.13+iz*smallpitch
        if abs(cx)>SHRINE_HALF-0.08 or cz>SHRINE_EAVE-0.06: continue
        # Leave a clean aperture for the pointed entrance and its arch bands.
        if cz<DOOR_APEX+0.12 and abs(cx)<1.68: continue
        pat=(ix*7+iz*11)%17
        mat=("Tile_Cobalt_Glaze" if pat not in (1,5,10) else
             "Tile_Turquoise_Glaze" if pat==1 else
             "Tile_Ivory_Glaze" if pat==5 else "Tile_Gold_Glaze")
        block(f"SHRINE_FACADE_TILE_{ix+18:02d}_{iz+1:02d}",mat,cx,cz,
              small,small,14.43,0.065,0.007)
# A dark recessed central door panel set behind the geometric arch frame.
block("SHRINE_DOOR_LEAF","Tile_Deep_Blue_Glaze",0,1.30,1.56,2.45,14.10,0.06,0.015)

# Dome drum and individually segmented turquoise dome tesserae.
DRUM_CX,DRUM_CY=0.0,SHRINE_Y
DRUM_R=1.47
for row in range(3):
    z0=SHRINE_EAVE+row*0.19;z1=z0+0.175
    for s in range(24):
        a0=2*math.pi*s/24+0.008;a1=2*math.pi*(s+1)/24-0.008
        mat="Tile_Turquoise_Glaze" if (s+row)%5 else "Tile_Ivory_Glaze"
        cylinder_panel(f"DOME_DRUM_TILE_R{row+1}_{s+1:02d}",mat,
                       DRUM_CX,DRUM_CY,DRUM_R,z0,z1,a0,a1)
# Dome shell: 32 sectors by 18 rising courses with a softly bulbous Persian profile.
DOME_BASE=4.87
DOME_HEIGHT=2.65
DOME_RADIUS=1.70
DOME_ROWS=18
DOME_SECTORS=32
def dome_r(t):
    # Rounded lower shoulder, then a firm taper to the finial.
    return DOME_RADIUS*(max(0.0,1.0-t**1.65)**0.64)*(0.94+0.12*math.sin(math.pi*t))
for row in range(DOME_ROWS):
    t0=row/DOME_ROWS+0.002;t1=(row+1)/DOME_ROWS-0.002
    r0=dome_r(t0);r1=dome_r(t1)
    z0=DOME_BASE+DOME_HEIGHT*t0;z1=DOME_BASE+DOME_HEIGHT*t1
    for s in range(DOME_SECTORS):
        a0=2*math.pi*s/DOME_SECTORS+0.003
        a1=2*math.pi*(s+1)/DOME_SECTORS-0.003
        v=[(DRUM_CX+r0*math.cos(a0),DRUM_CY+r0*math.sin(a0),z0),
           (DRUM_CX+r0*math.cos(a1),DRUM_CY+r0*math.sin(a1),z0),
           (DRUM_CX+r1*math.cos(a1),DRUM_CY+r1*math.sin(a1),z1),
           (DRUM_CX+r1*math.cos(a0),DRUM_CY+r1*math.sin(a0),z1)]
        if row in (4,10,15): mat="Tile_Gold_Glaze"
        elif (s+row)%9==0: mat="Tile_Ivory_Glaze"
        else: mat="Tile_Turquoise_Glaze" if (s+row)%4 else "Tile_Teal_Glaze"
        face_quad(f"DOME_SCALES_R{row+1:02d}_S{s+1:02d}",mat,v)
# Dome finial.
block("DOME_FINIAL_BASE","Tile_Gold_Glaze",0,DOME_BASE+DOME_HEIGHT+0.08,0.24,0.16,
      DRUM_CY-0.08,0.16,0.008)
block("DOME_FINIAL_NECK","Tile_Gold_Glaze",0,DOME_BASE+DOME_HEIGHT+0.24,0.075,0.28,
      DRUM_CY-0.04,0.08,0.006)

# Twin patterned minarets, with segmented shafts, projecting galleries and crowns.
for side,label in [(-1,"L"),(1,"R")]:
    mx=side*1.92;my=SHRINE_Y
    # octagonal tiled plinth
    horizontal_slab(f"MINARET_{label}_BASE","Stone_Carved",mx,my,4.18,0.88,0.88,0.32,8)
    horizontal_slab(f"MINARET_{label}_BASE_BAND","Tile_Cobalt_Glaze",mx,my,4.50,0.74,0.74,0.12,8)
    # lower and upper glazed shaft drum, individual scale panels
    shaft_spans=[(4.62,7.20,0.29),(7.53,8.43,0.235)]
    for level,(za,zb,rad) in enumerate(shaft_spans):
        rows=int((zb-za)/0.20)
        for row in range(rows):
            z0=za+row*(zb-za)/rows;z1=za+(row+1)*(zb-za)/rows-0.014
            for s in range(16):
                a0=2*math.pi*s/16+0.008;a1=2*math.pi*(s+1)/16-0.008
                mat=("Tile_Turquoise_Glaze" if (s+row)%5 else
                     "Tile_Cobalt_Glaze" if level==0 else "Tile_Ivory_Glaze")
                cylinder_panel(f"MINARET_{label}_SHAFT_{level+1}_{row+1:02d}_{s+1:02d}",
                               mat,mx,my,rad,z0,z1,a0,a1)
    # Two prominent muqarnas-like balcony rings.
    for n,z in enumerate((7.12,8.38)):
        horizontal_slab(f"MINARET_{label}_GALLERY_{n+1}_STONE","Stone_Carved",
                         mx,my,z,0.88 if n==0 else 0.70,0.88 if n==0 else 0.70,0.17,12)
        horizontal_slab(f"MINARET_{label}_GALLERY_{n+1}_BLUE","Tile_Cobalt_Glaze",
                         mx,my,z+0.17,0.82 if n==0 else 0.64,0.82 if n==0 else 0.64,0.07,12)
        bal_r=0.37 if n==0 else 0.29
        for s in range(12):
            a0=2*math.pi*s/12+0.006;a1=2*math.pi*(s+1)/12-0.006
            cylinder_panel(f"MINARET_{label}_BALUSTRADE_{n+1}_{s+1:02d}",
                           "Tile_Ivory_Glaze",mx,my,bal_r,z+0.24,z+0.48,a0,a1)
    # Open belfry crown and an eight-panel pointed cap.
    crownz=8.48
    horizontal_slab(f"MINARET_{label}_CROWN_RING","Tile_Gold_Glaze",mx,my,crownz,
                    0.54,0.54,0.10,8)
    for s in range(8):
        a0=2*math.pi*s/8;a1=2*math.pi*(s+1)/8
        verts=[(mx+0.25*math.cos(a0),my+0.25*math.sin(a0),crownz+0.10),
               (mx+0.25*math.cos(a1),my+0.25*math.sin(a1),crownz+0.10),
               (mx,my,crownz+0.80)]
        face_quad(f"MINARET_{label}_SPIRE_PANEL_{s+1:02d}","Tile_Turquoise_Glaze",verts)
    block(f"MINARET_{label}_FINIAL","Tile_Gold_Glaze",mx,crownz+0.90,0.075,0.22,my-0.04,0.08,0.005)

# Flanking courtyard arcades: four pointed openings to either side of the shrine,
# with tile archivolts, square piers and dark recesses behind them.
ARCADE_Y=12.52
BAY=1.48
ARC_INNER=0.56
ARC_SHOULDER=1.92
ARC_APEX=2.67
for side,label in [(-1,"L"),(1,"R")]:
    # five supporting piers across four bays
    for i in range(5):
        x=side*(2.50+i*BAY)
        block(f"RIWAQ_{label}_PIER_{i+1:02d}_CORE","Structure_Core",
              x,1.50,0.34,3.00,ARCADE_Y,0.72,0.012)
        for row in range(12):
            z=0.16+row*0.235
            mat=brick_mats[(i+row)%len(brick_mats)]
            block(f"RIWAQ_{label}_PIER_{i+1:02d}_BRICK_{row+1:02d}",mat,
                  x,z+0.09,0.36,0.18,ARCADE_Y-0.07,0.10,0.006)
        block(f"RIWAQ_{label}_CAPITAL_{i+1:02d}","Tile_Turquoise_Glaze",
              x,2.92,0.48,0.15,ARCADE_Y-0.10,0.80,0.012)
    # continuous upper beam
    block(f"RIWAQ_{label}_CORNICE","Stone_Carved",side*(2.50+1.48*2),3.12,
          6.05,0.32,ARCADE_Y-0.03,0.80,0.018)
    for bay in range(4):
        center=side*(2.50+(bay+0.5)*BAY)
        # dark pointed opening set at the rear plane, unobstructed below the arch
        poly=custom_arch_polygon(ARC_INNER,ARC_SHOULDER,ARC_APEX)
        poly=[(x+center,z) for x,z in poly]
        prism(f"RIWAQ_{label}_BAY_{bay+1:02d}_DARK_RECESS","Tile_Deep_Blue_Glaze",
              poly,13.19,13.27)
        for band,(wi,wo,mat) in enumerate([
            (0.56,0.64,"Tile_Turquoise_Glaze"),(0.65,0.73,"Tile_Ivory_Glaze"),
            (0.74,0.82,"Brick_Honey")]):
            for archside,letter in [(-1,"L"),(1,"R")]:
                for s in range(9):
                    t0=s/9+0.004;t1=(s+1)/9-0.004
                    p=[custom_arch_point(wo,archside,t0,ARC_SHOULDER,ARC_APEX),
                       custom_arch_point(wo,archside,t1,ARC_SHOULDER,ARC_APEX),
                       custom_arch_point(wi,archside,t1,ARC_SHOULDER,ARC_APEX),
                       custom_arch_point(wi,archside,t0,ARC_SHOULDER,ARC_APEX)]
                    p=[(x+center,z) for x,z in p]
                    prism(f"RIWAQ_{label}_BAY_{bay+1:02d}_ARCH_{band+1}_{letter}_{s+1:02d}",
                          mat,p,ARCADE_Y-0.14,ARCADE_Y+0.02)

# Courtyard paving: large square limestone slabs with narrow joints, extending
# from the gateway threshold to the arcades and shrine.
PAV_W=0.78;PAV_D=0.72;PAV_G=0.025
for ix in range(-12,13):
    for iy in range(0,22):
        cx=ix*(PAV_W+PAV_G)
        cy=1.36+iy*(PAV_D+PAV_G)
        shade=(ix*7+iy*3)%7
        mat="Stone_Carved" if shade not in (1,5) else "Mortar_Lime"
        rect_slab(f"COURTYARD_PAVING_X{ix+13:02d}_Y{iy+1:02d}",mat,
                  cx,cy,0.005,PAV_W,PAV_D,0.055)

# Planter boxes, trunks and tiered low-poly cypress/evergreen forms flank the walk.
def cone_frustum(name,mat,cx,cy,z0,z1,r0,r1,sides=8):
    verts=[]
    for z,r in ((z0,r0),(z1,r1)):
        for s in range(sides):
            a=2*math.pi*s/sides
            verts.append((cx+r*math.cos(a),cy+r*math.sin(a),z))
    faces=[tuple(range(sides-1,-1,-1)),tuple(range(sides,2*sides))]
    for s in range(sides):
        n=(s+1)%sides
        faces.append((s,n,sides+n,sides+s))
    add(name,mat,verts,faces)

for side,label in [(-1,"L"),(1,"R")]:
    for idx,(ax,ay) in enumerate([(2.65,3.9),(3.10,6.8),(2.60,9.8),(4.25,11.2)]):
        tx=side*ax
        block(f"COURTYARD_{label}_PLANTER_{idx+1}","Stone_Carved",tx,0.30,0.82,0.58,ay-0.43,0.86,0.03)
        cone_frustum(f"COURTYARD_{label}_TREE_TRUNK_{idx+1}","Wood_Dark",tx,ay,0.58,1.72,0.095,0.055,8)
        # Three overlapping evergreen tiers, narrowing to a sharp crown.
        for tier,(z0,z1,r0,r1) in enumerate([(1.05,2.40,0.70,0.05),
                                               (1.72,3.18,0.58,0.035),
                                               (2.40,3.75,0.44,0.015)]):
            cone_frustum(f"COURTYARD_{label}_TREE_{idx+1}_FOLIAGE_{tier+1}",
                         "Foliage_Evergreen",tx,ay,z0,z1,r0,r1,9)

# Decorative courtyard lamps on slender stone posts, echoing the lanterns in the photo.
for side,label in [(-1,"L"),(1,"R")]:
    lx=side*2.35;ly=5.45
    block(f"LANTERN_{label}_FOOT","Stone_Carved",lx,0.20,0.32,0.40,ly-0.16,0.32,0.015)
    block(f"LANTERN_{label}_POST","Brick_Shadow",lx,1.16,0.12,1.55,ly-0.06,0.12,0.008)
    # Four gold uprights and a glowing-colored glass box (geometry only).
    block(f"LANTERN_{label}_GLASS","Tile_Ivory_Glaze",lx,2.02,0.43,0.46,ly-0.22,0.44,0.018)
    for dx in (-0.22,0.22):
        for dy in (-0.22,0.22):
            # narrow square corner posts
            horizontal_slab(f"LANTERN_{label}_CORNER_{dx}_{dy}","Tile_Gold_Glaze",
                            lx+dx,ly+dy,1.78,0.045,0.045,0.54,4)
    block(f"LANTERN_{label}_ROOF","Tile_Cobalt_Glaze",lx,2.34,0.57,0.12,ly-0.285,0.57,0.01)


def export():
    with MTL.open("w",encoding="utf8") as f:
        f.write("# Material library | bare materials only; no image textures\n")
        for name,(rgb,gloss) in materials.items():
            ks=0.48 if gloss else 0.12
            f.write(f"\nnewmtl {name}\nKa 0.08 0.08 0.08\nKd {rgb[0]:.4f} {rgb[1]:.4f} {rgb[2]:.4f}\nKs {ks:.3f} {ks:.3f} {ks:.3f}\nNs {210 if gloss else 30}\nillum 2\n")
    with OBJ.open("w",encoding="utf8") as f:
        f.write("# Persian monumental gateway matching supplied reference | metres | Z-up | front toward -Y\n")
        f.write(f"mtllib {MTL.name}\n")
        vbase=uvbase=1
        for name,mat,verts,faces in parts:
            f.write(f"\no {name}\nusemtl {mat}\ns off\n")
            if not verts: continue
            ranges=[max(v[a] for v in verts)-min(v[a] for v in verts) for a in range(3)]
            axes=sorted(range(3),key=lambda a:ranges[a],reverse=True)[:2]
            a,b=axes
            va=min(v[a] for v in verts); vb=min(v[b] for v in verts)
            da=max(ranges[a],1e-6); db=max(ranges[b],1e-6)
            for v in verts: f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
            for v in verts: f.write(f"vt {(v[a]-va)/da:.6f} {(v[b]-vb)/db:.6f}\n")
            for face in faces:
                ids=list(face)
                f.write("f "+" ".join(f"{vbase+i}/{uvbase+i}" for i in ids)+"\n")
            vbase+=len(verts); uvbase+=len(verts)
    print(f"Created {OBJ.name}: {len(parts):,} separate bricks, tiles, and architectural parts")

if __name__=="__main__": export()
