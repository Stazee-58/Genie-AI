import math

# Tâm (centroid) của mỗi nhóm màu: (skin_R, skin_G, skin_B, hair_R, hair_G, hair_B)
_CENTROIDS = {
    "Warm Spring":  (243.852, 202.359, 180.464, 108.651,  83.833,  70.887),
    "Light Spring": (243.986, 226.830, 215.576, 214.960, 204.645, 204.885),
    "Clear Spring": (227.570, 174.053, 143.618,  35.910,  31.950,  38.027),
    "Light Summer": (231.460, 184.660, 165.630, 158.000,  98.157,  81.982),
    "Soft Summer":  (226.530, 206.212, 163.026,  92.924,  78.635,  72.345),
    "Cool Summer":  (203.620, 152.978, 126.393,  17.667,  18.890,  19.287),
    "Soft Autumn":  (222.086, 177.840, 145.870, 123.920,  90.707,  72.247),
    "Deep Autumn":  (203.960, 147.296, 113.128,  44.397,  35.099,  26.589),
    "Warm Autumn":  (179.868, 128.390, 100.100, 142.795,  91.614,  73.373),
    "Deep Winter":  (226.107, 171.970, 144.297,  17.667,  18.890,  19.287),
    "Clear Winter": (245.454, 207.065, 191.890, 110.542,  90.260,  77.610),
    "Cool Winter":  (222.420, 146.424, 167.488,  54.000,  37.069,  34.116),
}


def personal_color(skin_r_or_tuple, skin_g_or_tuple=None, skin_b=None,
                   hair_r=None, hair_g=None, hair_b=None):
    """
    Xác định nhóm màu cá nhân dựa trên khoảng cách Euclidean gần nhất.
    Luôn trả về nhóm gần nhất — không bao giờ trả về None.

    Hỗ trợ 2 cách gọi:
      personal_color(skin_tuple, hair_tuple)           <- 2 tuple (r,g,b)
      personal_color(sr, sg, sb, hr, hg, hb)           <- 6 số riêng lẻ
    """
    # Phát hiện cách gọi
    if isinstance(skin_r_or_tuple, (tuple, list)):
        # Cách gọi: personal_color((r,g,b), (r,g,b))
        sr, sg, sb = skin_r_or_tuple
        hr, hg, hb = skin_g_or_tuple  # second arg is hair tuple
    else:
        # Cách gọi: personal_color(r, g, b, r, g, b)
        sr, sg, sb = skin_r_or_tuple, skin_g_or_tuple, skin_b
        hr, hg, hb = hair_r, hair_g, hair_b

    input_vec = (sr, sg, sb, hr, hg, hb)

    best_color = "Light Summer"
    best_dist  = float('inf')

    for color_name, centroid in _CENTROIDS.items():
        dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(input_vec, centroid)))
        print(f'[DEBUG] {color_name}: distance = {dist:.2f}')
        if dist < best_dist:
            best_dist  = dist
            best_color = color_name

    print(f'[DEBUG] Personal color result: {best_color} (dist={best_dist:.2f})')
    return best_color