import json, os, sys, urllib.request

U = os.environ.get("MAKEFUN_ENV_URL") or ""
MATE = 100000
VAL = {"p": 100, "n": 320, "b": 330, "r": 500, "q": 900, "k": 0}
PM = [0,0,0,0,0,0,0,0, 5,10,10,-20,-20,10,10,5, 5,-5,-10,0,0,-10,-5,5,
      0,0,0,20,20,0,0,0, 5,5,10,25,25,10,5,5, 10,10,20,30,30,20,10,10,
      50,50,50,50,50,50,50,50, 0,0,0,0,0,0,0,0]
NM = [-50,-40,-30,-30,-30,-30,-40,-50, -40,-20,0,5,5,0,-20,-40,
      -30,5,10,15,15,10,5,-30, -30,0,15,20,20,15,0,-30,
      -30,5,15,20,20,15,5,-30, -30,0,10,15,15,10,0,-30,
      -40,-20,0,0,0,0,-20,-40, -50,-40,-30,-30,-30,-30,-40,-50]
BM = [-20,-10,-10,-10,-10,-10,-10,-20, -10,5,0,0,0,0,5,-10,
      -10,10,10,10,10,10,10,-10, -10,0,10,10,10,10,0,-10,
      -10,5,5,10,10,5,5,-10, -10,0,5,10,10,5,0,-10,
      -10,0,0,0,0,0,0,-10, -20,-10,-10,-10,-10,-10,-10,-20]
RM = [0,0,0,5,5,0,0,0, -5,0,0,0,0,0,0,-5, -5,0,0,0,0,0,0,-5,
      -5,0,0,0,0,0,0,-5, -5,0,0,0,0,0,0,-5, -5,0,0,0,0,0,0,-5,
      5,10,10,10,10,10,10,5, 0,0,0,0,0,0,0,0]
QM = [-20,-10,-10,-5,-5,-10,-10,-20, -10,0,5,0,0,0,0,-10,
      -10,5,5,5,5,5,0,-10, 0,0,5,5,5,5,0,-5, -5,0,5,5,5,5,0,-5,
      -10,0,5,5,5,5,0,-10, -10,0,0,0,0,0,0,-10, -20,-10,-10,-5,-5,-10,-10,-20]
KM = [-30,-40,-40,-50,-50,-40,-40,-30, -30,-40,-40,-50,-50,-40,-40,-30,
      -30,-40,-40,-50,-50,-40,-40,-30, -30,-40,-40,-50,-50,-40,-40,-30,
      -20,-30,-30,-40,-40,-30,-30,-20, -10,-20,-20,-20,-20,-20,-20,-10,
      20,20,0,0,0,0,20,20, 20,30,10,0,0,10,30,20]
PST = {"p": PM, "n": NM, "b": BM, "r": RM, "q": QM, "k": KM}


def tbl(ds):
    t = [[] for _ in range(64)]
    for i in range(64):
        r, c = divmod(i, 8)
        for dr, dc in ds:
            R, C = r + dr, c + dc
            if 0 <= R < 8 and 0 <= C < 8:
                t[i].append(R * 8 + C)
    return t


NN = tbl(((1,2),(2,1),(-1,2),(-2,1),(1,-2),(2,-1),(-1,-2),(-2,-1)))
KK = tbl(((-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)))
RD = ((1,0),(-1,0),(0,1),(0,-1))
BD = ((1,1),(1,-1),(-1,1),(-1,-1))
NODES = 0
CAP = 0
KI = [[] for _ in range(80)]
HI = [0] * 4096


class Stop(Exception):
    pass


def parse(fen):
    rows = fen.split()[0].split("/")
    b = ["."] * 64
    for r, row in enumerate(rows):
        f = 0
        for ch in row:
            if ch.isdigit():
                f += int(ch)
            else:
                b[(7 - r) * 8 + f] = ch
                f += 1
    parts = fen.split()
    w = parts[1] == "w"
    mask = 0
    for ch in parts[2]:
        mask |= {"K": 1, "Q": 2, "k": 4, "q": 8}.get(ch, 0)
    ep = -1
    if len(parts) > 3 and parts[3] != "-":
        ep = "abcdefgh".index(parts[3][0]) + (int(parts[3][1]) - 1) * 8
    return b, w, mask, ep


def ev(b):
    s = 0
    nb = [0, 0]
    for i, p in enumerate(b):
        if p == ".":
            continue
        x = p.lower()
        v = VAL[x] + PST[x][i if p.isupper() else i ^ 56]
        if p.isupper():
            s += v
            if x == "b": nb[0] += 1
        else:
            s -= v
            if x == "b": nb[1] += 1
    if nb[0] > 1: s += 30
    if nb[1] > 1: s -= 30
    return s


def gen(b, w, cast, ep):
    ms = []
    for i, p in enumerate(b):
        if p == "." or p.isupper() != w:
            continue
        x = p.lower()
        if x == "p":
            d = 8 if w else -8
            r = i // 8
            j = i + d
            if 0 <= j < 64 and b[j] == ".":
                if j // 8 in (0, 7):
                    ms.append((i, j, "q")); ms.append((i, j, "n"))
                else:
                    ms.append((i, j, ""))
                if (r == 1 and w) or (r == 6 and not w):
                    k = i + 2 * d
                    if b[k] == ".":
                        ms.append((i, k, ""))
            for dc in (-1, 1):
                c = i % 8 + dc
                if 0 <= c < 8:
                    j = i + d + dc
                    if b[j] != "." and b[j].isupper() != w:
                        if j // 8 in (0, 7):
                            ms.append((i, j, "q")); ms.append((i, j, "n"))
                        else:
                            ms.append((i, j, ""))
                    elif j == ep:
                        ms.append((i, j, ""))
        elif x == "n":
            for j in NN[i]:
                if b[j] == "." or b[j].isupper() != w:
                    ms.append((i, j, ""))
        elif x == "k":
            for j in KK[i]:
                if b[j] == "." or b[j].isupper() != w:
                    ms.append((i, j, ""))
            if w:
                if cast & 1 and b[4] == "K" and not b[5] + b[6] and b[7] == "R":
                    ms.append((4, 6, ""))
                if cast & 2 and b[4] == "K" and not b[1] + b[2] + b[3] and b[0] == "R":
                    ms.append((4, 2, ""))
            else:
                if cast & 4 and b[60] == "k" and not b[61] + b[62] and b[63] == "r":
                    ms.append((60, 62, ""))
                if cast & 8 and b[60] == "k" and not b[57] + b[58] + b[59] and b[56] == "r":
                    ms.append((60, 58, ""))
        else:
            ds = RD if x == "r" else BD if x == "b" else RD + BD
            for dr, dc in ds:
                r, c = divmod(i, 8)
                while True:
                    r += dr; c += dc
                    if not (0 <= r < 8 and 0 <= c < 8):
                        break
                    j = r * 8 + c
                    q = b[j]
                    if q == ".":
                        ms.append((i, j, ""))
                    else:
                        if q.isupper() != w:
                            ms.append((i, j, ""))
                        break
    return ms


def move(b, w, cast, ep, f, t, pr):
    nb = b[:]
    p = nb[f]
    nb[t] = (pr.upper() if w else pr) if pr else p
    nb[f] = "."
    if p.lower() == "k" and abs(t - f) == 2:
        rf = (7 if t > f else 0) + (56 if t >= 56 else 0)
        rt = t + (-1 if t > f else 1)
        nb[rt] = nb[rf]
        nb[rf] = "."
    if p.lower() == "p" and t % 8 != f % 8 and b[t] == ".":
        nb[(f // 8) * 8 + t % 8] = "."
    if f == 4: cast &= ~3
    elif f == 60: cast &= ~12
    elif f == 0: cast &= ~2
    elif f == 7: cast &= ~1
    elif f == 56: cast &= ~8
    elif f == 63: cast &= ~4
    if t == 0: cast &= ~2
    elif t == 7: cast &= ~1
    elif t == 56: cast &= ~8
    elif t == 63: cast &= ~4
    ne = (f + t) // 2 if p.lower() == "p" and abs(t - f) == 16 else -1
    return nb, not w, cast, ne


def order(b, ms, ply):
    out = []
    for m in ms:
        v = b[m[1]]
        s = 8000 if m[2] else 0
        if v != ".":
            s += 1000 * VAL[v.lower()] - VAL[b[m[0]].lower()]
        if m in KI[ply]:
            s += 500
        out.append((s + HI[m[0] * 64 + m[1]], m))
    out.sort(key=lambda x: -x[0])
    return [m for s, m in out]


def ne(b, w, cast, ep, d, a, be, ply):
    global NODES
    NODES += 1
    if NODES > CAP:
        raise Stop
    if d <= 0:
        return qs(b, w, cast, ep, a, be, ply)
    ms = gen(b, w, cast, ep)
    if not ms:
        return 0
    best = -MATE
    for m in order(b, ms, ply):
        f, t, pr = m
        if b[t] != "." and b[t].lower() == "k":
            return MATE - ply
        nb, nw, nc, ne2 = move(b, w, cast, ep, f, t, pr)
        v = -ne(nb, nw, nc, ne2, d - 1, -be, -a, ply + 1)
        if v > best:
            best = v
        if v > a:
            a = v
        if a >= be:
            if b[t] == "." and not pr:
                KI[ply] = [m] + KI[ply][:1]
                HI[f * 64 + t] += d * d
            break
    return best


def qs(b, w, cast, ep, a, be, ply, qd=0):
    global NODES
    NODES += 1
    if NODES > CAP:
        raise Stop
    s = ev(b) if w else -ev(b)
    if qd > 4 or s >= be:
        return s
    if s > a:
        a = s
    ms = [m for m in gen(b, w, cast, ep) if b[m[1]] != "." or m[2]]
    for m in order(b, ms, ply):
        f, t, pr = m
        if b[t] != "." and b[t].lower() == "k":
            return MATE - ply
        nb, nw, nc, ne2 = move(b, w, cast, ep, f, t, pr)
        v = -qs(nb, nw, nc, ne2, -be, -a, ply + 1, qd + 1)
        if v > a:
            a = v
        if a >= be:
            break
    return a


def alg(u):
    return ("abcdefgh".index(u[0]) + (int(u[1]) - 1) * 8,
            "abcdefgh".index(u[2]) + (int(u[3]) - 1) * 8,
            u[4] if len(u) > 4 else "")


def uci(m):
    f, t, pr = m
    return "abcdefgh"[f % 8] + str(f // 8 + 1) + "abcdefgh"[t % 8] + str(t // 8 + 1) + pr


def best(fen, legal):
    global NODES, CAP, KI, HI
    b, w, cast, ep = parse(fen)
    root = [alg(u) for u in legal]
    KI = [[] for _ in range(80)]
    HI = [0] * 4096
    CAP = int(os.environ.get("MF_CAP", "120000"))
    NODES = 0
    pick = root[0]
    for d in range(1, 20):
        a = -MATE
        cand = None
        try:
            ms = order(b, root, 0)
            if pick in ms:
                ms.remove(pick); ms.insert(0, pick)
            for m in ms:
                f, t, pr = m
                nb, nw, nc, ne2 = move(b, w, cast, ep, f, t, pr)
                v = -ne(nb, nw, nc, ne2, d - 1, -MATE, -a, 1)
                if v > a:
                    a = v
                    cand = m
            if cand is not None:
                pick = cand
        except Stop:
            break
    return uci(pick)


def post(path, body):
    req = urllib.request.Request(U + path, data=json.dumps(body).encode(),
                                 headers={"content-type": "application/json"})
    with urllib.request.urlopen(req) as r:
        return json.load(r)


if __name__ == "__main__":
  while True:
    g = post("/game", {})
    if g["status"] == "done":
        break
    while g["status"] == "your_move":
        mv = best(g["fen"], g["legal_moves"])
        if mv not in g["legal_moves"]:
            mv = g["legal_moves"][0]
        g = post("/move", {"game": g["game"], "move": mv})
    print("game %s: %s" % (g["game"], g["outcome"]), file=sys.stderr)
  print("done: %s won" % g.get("wins"), file=sys.stderr)
