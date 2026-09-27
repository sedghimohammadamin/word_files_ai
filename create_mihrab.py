#!/usr/bin/env python3
"""Generate a texture-ready, individually modular Persian mihrab model as OBJ/MTL.

Run with Python 3 (no third-party packages required):
    python3 create_mihrab.py

The exported model is in metres, front faces toward -Y, and has per-piece UVs.
"""
from pathlib import Path
import math

OUT = Path(__file__).resolve().parent
OBJ = OUT / "mihrab_qom.obj"
MTL = OUT / "mihrab_qom.mtl"

# Each object is a separate mesh part. Coordinates are (x, y, z); UVs are
# normalized from the part's own front-facing X/Z bounds for later texture work.
objects = []
materials = {
    "Brick_Red_Clay": ((0.48, 0.19, 0.105), 0.0),
    "Brick_Warm_Clay": ((0.61, 0.29, 0.16), 0.0),
    "Brick_Light_Clay": ((0.70, 0.39, 0.23), 0.0),
    "Mortar_Stone": ((0.66, 0.62, 0.53), 0.0),
    "Tile_Cobalt_Glaze": ((0.035, 0.105, 0.43), 0.82),
    "Tile_Turquoise_Glaze": ((0.02, 0.48, 0.52), 0.82),
    "Tile_Lapis_Glaze": ((0.08, 0.24, 0.70), 0.82),
    "Tile_Ivory_Glaze": ((0.88, 0.78, 0.59), 0.72),
    "Tile_Teal_Glaze": ((0.015, 0.30, 0.30), 0.82),
    "Niche_Deep_Blue": ((0.018, 0.065, 0.20), 0.62),
    "Backing_Limestone": ((0.59, 0.54, 0.44), 0.0),
}


def add(name, material, verts, faces):
    objects.append((name, material, verts, faces))


def chamfer_rect(x0, x1, z0, z1, c):
    c = max(0.0, min(c, (x1-x0)*0.2, (z1-z0)*0.2))
    if c < 1e-6:
        return [(x0,z0),(x1,z0),(x1,z1),(x0,z1)]
    return [(x0+c,z0),(x1-c,z0),(x1,z0+c),(x1,z1-c),
            (x1-c,z1),(x0+c,z1),(x0,z1-c),(x0,z0+c)]


def prism(name, material, polygon, y_front, y_back):
    """Extrude an X/Z polygon, with the face toward -Y."""
    n = len(polygon)
    verts = [(x,y_front,z) for x,z in polygon] + [(x,y_back,z) for x,z in polygon]
    faces = [tuple(range(n-1,-1,-1)), tuple(range(n,2*n))]
    for i in range(n):
        j = (i+1) % n
        faces.append((i,j,n+j,n+i))
    add(name, material, verts, faces)


def block(name, material, x, z, w, h, yfront, depth, bevel=0.012):
    prism(name, material, chamfer_rect(x-w/2,x+w/2,z-h/2,z+h/2,bevel), yfront, yfront+depth)


def arch_z(width, t):
    """Pointed Persian arch curve from shoulder (t=0) to apex (t=1)."""
    shoulder, apex = 3.43, 5.12 + (width-1.15)*0.72
    return shoulder + (apex-shoulder)*(1.0-(1.0-t)**1.55)


def arch_point(width, side, t):
    return side*width*(1.0-t), arch_z(width,t)


def arch_tile(name, material, win, wout, side, t0, t1, yfront, depth):
    # A separate four-sided voussoir/tile following the curved intrados.
    poly = [arch_point(wout,side,t0), arch_point(wout,side,t1),
            arch_point(win,side,t1), arch_point(win,side,t0)]
    prism(name, material, poly, yfront, yfront+depth)


def face_strip(name, material, front_a, front_b, back_a, back_b, yf, yb, thickness=0.035):
    # Four-corner surface extrusion, used for individually modeled niche reveals.
    poly = [front_a, front_b, back_b, back_a]
    prism(name, material, poly, yf, yb)


# Limestone backup is built around (not across) the niche aperture, so the
# recess is a real void and its tiled back panel remains visible from the front.
# All pieces are separate masonry meshes on a common structural datum.
wall_y, wall_depth = 0.22, 0.62
for side,label in [(-1,"L"),(1,"R")]:
    block(f"WALL_Backup_{label}_Lower_Pier", "Backing_Limestone",
          side*(1.16+2.86)/2, 1.715, 2.86-1.16, 3.43, wall_y, wall_depth, 0.0)
    pts=[(side*2.86,3.43),arch_point(1.16,side,0.0)]
    pts += [arch_point(1.16,side,i/24) for i in range(1,25)]
    pts += [(-2.86,5.12)] if side < 0 else [(2.86,5.12)]
    prism(f"WALL_Backup_{label}_Spandrel", "Backing_Limestone", pts, wall_y, wall_y+wall_depth)
block("WALL_Backup_Upper_Header", "Backing_Limestone", 0,5.78,5.72,1.32,wall_y,wall_depth,0.0)

# Individually laid running-bond clay bricks on the facade. The calculated
# opening mask keeps every brick outside the pointed niche and its tiled frame.
brick_w, brick_h, gap = 0.425, 0.205, 0.025
row_pitch, col_pitch = brick_h+gap, brick_w+gap
brick_mats = ["Brick_Red_Clay","Brick_Warm_Clay","Brick_Light_Clay"]
for row in range(25):
    z = 0.28 + row*row_pitch
    offset = (row % 2) * col_pitch/2
    col = 0
    x = -2.82 + offset
    while x <= 2.82:
        # Allow a gently uneven but measured mortar rhythm; brick dimensions
        # remain consistent and every masonry unit remains independently UV-able.
        jitter = ((row*17 + col*13) % 5 - 2) * 0.003
        cx = x + jitter
        cz = z + (((row*7+col*11)%3)-1)*0.002
        opening = False
        if abs(cx) < 1.16:
            if cz < 3.43:
                opening = True
            else:
                t = max(0.0, min(1.0, 1.0 - (abs(cx)/1.16)))
                boundary = arch_z(1.16,t)
                opening = cz < boundary + 0.16
        # Leave a clear surround for the ceramic archivolt (outer width 1.62).
        if abs(cx) < 1.67 and cz >= 3.23:
            t = max(0.0, min(1.0, 1.0 - abs(cx)/1.67))
            if cz < arch_z(1.67,t) + 0.10:
                opening = True
        if not opening and 0.12 < cz < 6.30 and abs(cx) < 2.83:
            mat = brick_mats[(row*3+col*5+(row//4)) % len(brick_mats)]
            block(f"BRICK_Course{row+1:02d}_Unit{col+1:02d}", mat,
                  cx,cz,brick_w,brick_h,-0.415,0.10,0.012)
        x += col_pitch
        col += 1

# Primary raised, glazed multi-ring arch surround. Ring segments are separate
# ceramic voussoirs, with small real grout gaps between each piece.
ring_specs = [
    (1.17,1.29,"Tile_Ivory_Glaze",0.155),
    (1.30,1.43,"Tile_Turquoise_Glaze",0.170),
    (1.44,1.57,"Tile_Cobalt_Glaze",0.188),
    (1.58,1.70,"Tile_Ivory_Glaze",0.205),
]
segments = 12
for ring,(wi,wo,mat,depth) in enumerate(ring_specs):
    for side,label in [(-1,"L"),(1,"R")]:
        for s in range(segments):
            t0 = s/segments + 0.004
            t1 = (s+1)/segments - 0.004
            # Ring-specific subtle alternation adds crafted variation, never
            # changes the geometry's modular tile boundaries.
            usemat = mat
            if ring == 1 and s % 4 == 1: usemat = "Tile_Teal_Glaze"
            if ring == 2 and s % 5 == 2: usemat = "Tile_Lapis_Glaze"
            arch_tile(f"ARCH_Ring{ring+1}_{label}_Tile{s+1:02d}",usemat,
                      wi,wo,side,t0,t1,-0.505-ring*0.008,depth)

# Vertical lower jamb surrounds, assembled from real ceramic units.
for side,label in [(-1,"L"),(1,"R")]:
    for band,(inner,outer,mat,yf,dep) in enumerate([
        (1.17,1.29,"Tile_Ivory_Glaze",-0.505,0.155),
        (1.30,1.43,"Tile_Turquoise_Glaze",-0.513,0.170),
        (1.44,1.57,"Tile_Cobalt_Glaze",-0.521,0.188),
        (1.58,1.70,"Tile_Ivory_Glaze",-0.529,0.205),
    ]):
        for k in range(8):
            z0 = 0.20+k*0.395+0.012
            z1 = z0+0.365
            x0,x1 = (inner,outer) if side > 0 else (-outer,-inner)
            block(f"JAMB_Ring{band+1}_{label}_Tile{k+1:02d}",mat,
                  side*(inner+outer)/2,(z0+z1)/2,outer-inner,z1-z0,yf,dep,0.01)

# Recessed back plane, plus independently glazed small square tiles laid as a
# texture-ready mosaic inside the actual niche opening.
block("NICHE_Recessed_Back_Panel", "Niche_Deep_Blue", 0,2.66,2.29,4.92,0.755,0.055,0.006)
tile_size, tile_gap = 0.19, 0.012
pitch = tile_size+tile_gap
for row in range(25):
    z0 = 0.28+row*pitch
    for col in range(11):
        x0 = -1.075+col*pitch
        cx,cz = x0+tile_size/2,z0+tile_size/2
        if abs(cx) > 1.10 or cz > arch_z(1.12,max(0.0,min(1.0,1.0-abs(cx)/1.12)))-0.04:
            continue
        # Compact, mirrored geometric motif; all tile units are separate objects.
        motif = (row+col) % 8
        mat = ("Tile_Cobalt_Glaze" if motif in (0,1,4,7) else
               "Tile_Turquoise_Glaze" if motif in (2,5) else
               "Tile_Ivory_Glaze" if motif == 3 else "Tile_Lapis_Glaze")
        block(f"NICHE_Mosaic_R{row+1:02d}_C{col+1:02d}",mat,
              cx,cz,tile_size,tile_size,0.680,0.035,0.008)

# Curved inner reveal: one individually modeled glazed/stone unit per course,
# creating depth from the front edge to the recessed back plane.
for side,label in [(-1,"L"),(1,"R")]:
    for s in range(16):
        t0,t1=s/16+0.002,(s+1)/16-0.002
        fa=arch_point(1.16,side,t0); fb=arch_point(1.16,side,t1)
        ba=arch_point(1.01,side,t0); bb=arch_point(1.01,side,t1)
        # Build the return across depth as its own four-sided mesh.
        verts=[(fa[0],-0.28,fa[1]),(fb[0],-0.28,fb[1]),
               (bb[0],0.64,bb[1]),(ba[0],0.64,ba[1])]
        faces=[(0,1,2,3)]
        add(f"REVEAL_Arch_{label}_{s+1:02d}",
            "Tile_Turquoise_Glaze" if s%4==0 else "Mortar_Stone",verts,faces)
    for k in range(8):
        z0=0.22+k*0.395; z1=z0+0.37
        xf=side*1.16; xb=side*1.01
        verts=[(xf,-0.28,z0),(xf,-0.28,z1),(xb,0.64,z1),(xb,0.64,z0)]
        add(f"REVEAL_Jamb_{label}_{k+1:02d}","Tile_Turquoise_Glaze" if k%4==0 else "Mortar_Stone",verts,[(0,1,2,3)])

# Matched spandrel mosaic plaques: faceted octagonal tiles in a crisp geometric
# rosette, individually selectable, not a printed texture.
for side,label in [(-1,"L"),(1,"R")]:
    cx,cz=side*2.02,4.30
    # shallow limestone/octagonal surround
    poly=[]
    for i in range(8):
        a=math.pi/8+i*math.pi/4
        poly.append((cx+0.53*math.cos(a),cz+0.53*math.sin(a)))
    prism(f"SPANDREL_{label}_Stone_Octagon","Mortar_Stone",poly,-0.440,0.035)
    for row in range(-3,4):
        for col in range(-3,4):
            tx=cx+col*0.132
            tz=cz+row*0.132
            if (tx-cx)**2+(tz-cz)**2 > 0.47**2: continue
            dist=abs(row)+abs(col)
            mat=("Tile_Ivory_Glaze" if dist==0 else
                 "Tile_Turquoise_Glaze" if (row-col)%2==0 else
                 "Tile_Cobalt_Glaze" if dist%2==0 else "Tile_Lapis_Glaze")
            block(f"SPANDREL_{label}_Mosaic_R{row+4}_C{col+4}",mat,
                  tx,tz,0.112,0.112,-0.466,0.045,0.012)

# Decorative bases and top course define the architectural footprint.
for side,label in [(-1,"L"),(1,"R")]:
    block(f"BASE_{label}_Stone_Platform","Mortar_Stone",side*1.44,0.16,0.64,0.30,-0.53,0.34,0.025)
    block(f"BASE_{label}_Blue_Inlay","Tile_Cobalt_Glaze",side*1.44,0.335,0.56,0.055,-0.545,0.355,0.008)
block("CROWN_Cap_Stone","Mortar_Stone",0,6.39,5.78,0.18,-0.45,0.32,0.025)


def export_obj():
    with MTL.open("w",encoding="utf8") as f:
        f.write("# Material library for texture-ready mihrab\n")
        for name,(rgb,gloss) in materials.items():
            f.write(f"\nnewmtl {name}\nKa 0.08 0.08 0.08\nKd {rgb[0]:.4f} {rgb[1]:.4f} {rgb[2]:.4f}\nKs {0.42 if gloss else 0.12:.3f} {0.42 if gloss else 0.12:.3f} {0.42 if gloss else 0.12:.3f}\nNs {180 if gloss else 28}\nillum 2\n")
    with OBJ.open("w",encoding="utf8") as f:
        f.write("# Texture-ready Persian mihrab | metres | Y depth, front toward -Y\n")
        f.write(f"mtllib {MTL.name}\n")
        vbase=uvbase=1
        for name,mat,verts,faces in objects:
            f.write(f"\no {name}\nusemtl {mat}\ns off\n")
            if not verts: continue
            xs=[v[0] for v in verts]; zs=[v[2] for v in verts]
            xmin,xmax=min(xs),max(xs); zmin,zmax=min(zs),max(zs)
            dx=max(xmax-xmin,1e-5); dz=max(zmax-zmin,1e-5)
            for x,y,z in verts: f.write(f"v {x:.6f} {y:.6f} {z:.6f}\n")
            for x,y,z in verts:
                f.write(f"vt {(x-xmin)/dx:.6f} {(z-zmin)/dz:.6f}\n")
            for face in faces:
                # OBJ positions and UVs are intentionally one-to-one; each
                # individual unit has a self-contained, normalized UV island.
                inds=[vbase+i for i in face]
                f.write("f "+" ".join(f"{i}/{uvbase+(i-vbase)}" for i in inds)+"\n")
            vbase+=len(verts); uvbase+=len(verts)
    print(f"Created {OBJ.name} with {len(objects):,} independently selectable parts")

if __name__ == "__main__":
    export_obj()
