# A-Maze-ing — Explications détaillées

---

## Vue d'ensemble

Ce projet génère des labyrinthes aléatoires. Voici le flux complet :

```
config.txt → parse_config() → MazeGenerator → generate() → maze.txt + affichage ASCII
```

1. On lit un fichier de configuration (dimensions, entrée, sortie, etc.)
2. On crée un MazeGenerator avec ces paramètres
3. On génère le labyrinthe (algorithme DFS)
4. On place le pattern "42" au centre
5. On résout avec BFS (plus court chemin)
6. On exporte en hexadécimal + on affiche en ASCII dans le terminal

---

## Les fichiers du projet

| Fichier | Rôle |
|---------|------|
| `mazegen/__init__.py` | Module réutilisable — contient la classe MazeGenerator |
| `a_maze_ing.py` | Script principal — parse le config, lance le menu interactif |
| `config.txt` | Configuration par défaut |
| `Makefile` | Automatisation (install, run, lint, clean, build) |
| `pyproject.toml` | Configuration pour construire le package pip |
| `.gitignore` | Fichiers à ignorer par git |

---

## Le module mazegen — Explication complète

---

### L'encodage des murs (le coeur du système)

Chaque cellule du labyrinthe a 4 murs possibles : Nord, Est, Sud, Ouest.
On encode les murs avec des **bits** dans un seul nombre :

```
Bit 0 (valeur 1) = Nord
Bit 1 (valeur 2) = Est
Bit 2 (valeur 4) = Sud
Bit 3 (valeur 8) = Ouest
```

Exemples :
```
0xF = 15 = 1111 en binaire = tous les murs fermés
0x0 = 0  = 0000 = tous les murs ouverts
0x3 = 3  = 0011 = Nord + Est fermés, Sud + Ouest ouverts
0xA = 10 = 1010 = Est + Ouest fermés, Nord + Sud ouverts
```

**Pourquoi des bits ?** Parce qu'on peut manipuler les murs individuellement avec des opérations binaires :

```python
N: int = 1    # 0001
E: int = 2    # 0010
S: int = 4    # 0100
W: int = 8    # 1000
```

```python
# Vérifier si un mur existe (AND binaire)
cell & N        # != 0 si le mur Nord existe

# Supprimer un mur (AND NOT)
cell &= ~N      # enlève le mur Nord, garde les autres

# Ajouter un mur (OR)
cell |= N        # ajoute le mur Nord
```

Exemple concret :
```python
cell = 0xF       # 1111 = tous les murs
cell &= ~E       # 1111 & ~0010 = 1111 & 1101 = 1101 = 13 = 0xD
                  # → le mur Est est enlevé, les autres restent
```

---

### La grille

```python
self.grid: list[list[int]] = [[0xF] * width for _ in range(height)]
```

C'est un tableau 2D. `grid[y][x]` donne le bitmask des murs de la cellule à la position (x, y).

Au départ, toutes les cellules ont tous leurs murs fermés (0xF = 15).

**Système de coordonnées :**
- `x` = colonne (0 à width-1), augmente vers la droite
- `y` = ligne (0 à height-1), augmente vers le bas
- Nord = y diminue, Sud = y augmente, Est = x augmente, Ouest = x diminue

```python
DX: dict[int, int] = {N: 0, S: 0, E: 1, W: -1}   # déplacement en x
DY: dict[int, int] = {N: -1, S: 1, E: 0, W: 0}    # déplacement en y
```

---

### Cohérence des murs entre cellules voisines

Quand on enlève un mur, il faut aussi l'enlever du côté du voisin. Si la cellule (3,2) n'a plus de mur Est, alors la cellule (4,2) ne doit plus avoir de mur Ouest.

```python
OPPOSITE: dict[int, int] = {N: S, S: N, E: W, W: E}

def _remove_wall(self, x: int, y: int, d: int) -> None:
    nx = x + DX[d]         # coordonnées du voisin
    ny = y + DY[d]
    self.grid[y][x] &= ~d              # enlève le mur de la cellule
    self.grid[ny][nx] &= ~OPPOSITE[d]  # enlève le mur opposé du voisin
```

Exemple :
```
Cellule (3,2) : on enlève le mur Est
→ grid[2][3] &= ~E         (enlève bit Est)
→ grid[2][4] &= ~W         (enlève bit Ouest du voisin)
```

---

### Le pattern "42"

Le "42" est dessiné avec des cellules totalement fermées (0xF) qui forment les chiffres 4 et 2.

Chaque chiffre fait 3 cellules de large × 5 cellules de haut :

```
"4" :          "2" :
X . X          X X X
X . X          . . X
X X X          X X X
. . X          X . .
. . X          X X X
```

Le "42" total fait 7×5 cellules (3 + 1 espace + 3).

On le place au **centre** du labyrinthe. Si le labyrinthe est trop petit (< 11×9), on ne le met pas et on affiche un warning.

Ces cellules sont marquées comme "visitées" par le DFS → l'algorithme les contourne, elles restent fermées.

---

### L'algorithme de génération : DFS (Recursive Backtracker)

C'est l'algorithme principal. Il crée un **labyrinthe parfait** (un seul chemin entre deux cellules quelconques).

**Le principe :** on part d'une cellule, on avance au hasard en cassant les murs, et quand on est bloqué on revient en arrière.

```
1. Partir de l'entrée, la marquer comme visitée
2. La mettre sur la pile (stack)
3. Tant que la pile n'est pas vide :
   a. Regarder la cellule en haut de la pile
   b. Trouver les voisins non-visités
   c. S'il y en a : en choisir un au hasard,
      casser le mur entre les deux,
      marquer le voisin comme visité,
      le mettre sur la pile
   d. S'il n'y en a pas : retirer la cellule de la pile (backtrack)
```

**Pourquoi ça crée un labyrinthe parfait ?** Parce que le DFS visite chaque cellule exactement une fois. L'ensemble des murs cassés forme un **arbre couvrant** (spanning tree) — il n'y a qu'un seul chemin entre deux cellules.

**Pourquoi itératif et pas récursif ?** Un labyrinthe 100×100 = 10 000 cellules. En récursif, ça ferait 10 000 appels imbriqués → dépassement de pile (stack overflow). La version itérative utilise une liste Python comme pile, pas de limite.

```python
def _generate_dfs(self) -> None:
    visited: set[tuple[int, int]] = {(sx, sy)}
    visited.update(self._pattern_cells)     # les cellules "42" sont déjà "visitées"
    stack: list[tuple[int, int]] = [(sx, sy)]

    while stack:
        x, y = stack[-1]                     # cellule actuelle (sommet de pile)
        nbrs = []                            # voisins non-visités
        for d in DIRECTIONS:
            nx, ny = x + DX[d], y + DY[d]
            if in_bounds(nx, ny) and (nx, ny) not in visited:
                nbrs.append((nx, ny, d))
        if nbrs:
            nx, ny, d = self._rng.choice(nbrs)  # choix aléatoire
            self._remove_wall(x, y, d)           # casse le mur
            visited.add((nx, ny))
            stack.append((nx, ny))               # avance
        else:
            stack.pop()                          # recule (backtrack)
```

---

### Labyrinthe imparfait (non-perfect)

Si `PERFECT=False`, on ajoute des boucles en cassant ~10% des murs restants.

**Contrainte :** pas de zone ouverte 3×3. Avant de casser un mur, on vérifie que ça ne crée pas un carré 3×3 sans murs internes.

```python
def _make_imperfect(self) -> None:
    # Collecter tous les murs restants
    # Les mélanger aléatoirement
    # En casser ~10%, sauf si ça crée un 3x3 ouvert
```

---

### Résolution : BFS (Breadth-First Search)

Pour trouver le **plus court chemin** de l'entrée à la sortie, on utilise le BFS.

**Pourquoi BFS et pas DFS ?** BFS explore les cellules **couche par couche** (distance 1, puis 2, puis 3...). Le premier chemin trouvé est garanti d'être le plus court. DFS pourrait trouver un chemin, mais pas forcément le plus court.

```
1. Mettre l'entrée dans une file (queue)
2. Tant que la file n'est pas vide :
   a. Prendre la première cellule de la file
   b. Si c'est la sortie → on a trouvé le chemin !
   c. Pour chaque direction sans mur :
      - Si le voisin n'est pas visité : l'ajouter à la file
        avec le chemin actuel + cette direction
```

```python
def solve(self) -> list[str]:
    queue = deque([(entry_x, entry_y, [])])
    visited = {self.entry}
    while queue:
        x, y, path = queue.popleft()
        if (x, y) == self.exit_pos:
            return path                    # trouvé !
        for d in DIRECTIONS:
            if not self._has_wall(x, y, d):
                nx, ny = x + DX[d], y + DY[d]
                if (nx, ny) not in visited:
                    visited.add((nx, ny))
                    queue.append((nx, ny, path + [DIR_CHAR[d]]))
    return []                              # pas de chemin
```

Le résultat est une liste comme `['E', 'E', 'S', 'E', 'N', ...]` — chaque lettre indique la direction à prendre depuis la cellule actuelle.

---

### Le format de sortie hexadécimal

```python
def to_hex_grid(self) -> list[str]:
    # Pour chaque ligne, pour chaque cellule,
    # convertir le bitmask en hexadécimal
    # 15 → 'F', 10 → 'A', 3 → '3'
```

Le fichier de sortie contient :
```
D539553955553D517913    ← ligne 0 (hex de chaque cellule)
97C693C69553C53C56AA    ← ligne 1
...                     ← lignes 2-14

0,0                     ← coordonnées de l'entrée
19,14                   ← coordonnées de la sortie
EESENEE...SSS           ← plus court chemin en N/E/S/W
```

---

### Le rendu ASCII

Chaque cellule est affichée comme un bloc 4×2 caractères :

```
+---+      ← mur Nord entre les +
|   |      ← murs Ouest et Est
+---+      ← mur Sud
```

Si un mur est absent, on met des espaces à la place.

Marqueurs spéciaux :
- `E` = entrée (en vert)
- `X` = sortie (en vert)
- `###` = cellule du pattern 42 (en jaune)
- `·` = chemin solution (en vert, si activé)

Les couleurs utilisent les **codes ANSI** :
```python
"\033[31m"   # rouge
"\033[32m"   # vert
"\033[33m"   # jaune
"\033[37m"   # blanc
"\033[0m"    # reset (retour à la couleur normale)
```

---

## Le script principal a_maze_ing.py

---

### Le parser de configuration

Lit un fichier ligne par ligne. Ignore les commentaires (`#`) et les lignes vides.
Sépare chaque ligne en `CLÉ=VALEUR`.

```python
def parse_config(filepath: str) -> dict[str, str]:
    config = {}
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            key, value = line.split('=', 1)
            config[key] = value
    return config
```

### La validation

Vérifie que toutes les clés obligatoires sont présentes, que les types sont corrects, que les coordonnées sont dans les bornes, etc.

### Le menu interactif

Boucle infinie qui :
1. Efface l'écran
2. Affiche le labyrinthe
3. Affiche le menu
4. Attend une touche de l'utilisateur
5. Exécute l'action correspondante

| Touche | Action |
|--------|--------|
| `r` | Régénère avec un nouveau seed (basé sur l'heure actuelle) |
| `s` | Affiche/cache le chemin solution |
| `c` | Change la couleur des murs (cycle de 7 couleurs) |
| `p` | Change la couleur du pattern 42 |
| `q` | Quitte |

---

## Le Makefile

| Commande | Ce qu'elle fait |
|----------|----------------|
| `make install` | Installe flake8, mypy, build |
| `make run` | Lance le programme avec config.txt |
| `make debug` | Lance avec le debugger Python (pdb) |
| `make clean` | Supprime __pycache__, .mypy_cache |
| `make lint` | flake8 + mypy avec les flags du sujet |
| `make lint-strict` | flake8 + mypy --strict |
| `make build` | Construit le package mazegen.whl |

---

## Le package pip

Le fichier `pyproject.toml` configure le build :

```toml
[project]
name = "mazegen"
version = "1.0.0"

[tool.setuptools]
packages = ["mazegen"]
```

Pour construire :
```bash
pip install build
python3 -m build
```

Ça crée `dist/mazegen-1.0.0-py3-none-any.whl` qu'on copie à la racine.

Pour installer dans un autre projet :
```bash
pip install mazegen-1.0.0-py3-none-any.whl
```

Puis :
```python
from mazegen import MazeGenerator
maze = MazeGenerator(20, 15, (0,0), (19,14), seed=42)
maze.generate()
```

---

## Concepts clés à retenir

| Concept | Explication |
|---------|-------------|
| Bitmask | Encoder plusieurs infos dans un seul nombre avec des bits |
| DFS | Depth-First Search — explore en profondeur puis backtrack |
| BFS | Breadth-First Search — explore couche par couche (plus court chemin) |
| Perfect maze | Un seul chemin entre deux cellules (arbre couvrant) |
| Spanning tree | Arbre qui connecte tous les nœuds sans cycle |
| ANSI codes | Séquences d'échappement pour colorer le terminal |
| Duck typing | Si ça a les bonnes méthodes, c'est compatible |
| Context manager | `with open()` ferme le fichier automatiquement |
| Seed | Graine aléatoire — même seed = même résultat |

---

## Questions possibles en soutenance

**"Pourquoi le Recursive Backtracker ?"**
"Parce qu'il garantit un labyrinthe parfait naturellement, il est simple à implémenter, et il produit des corridors longs et intéressants."

**"Comment tu garantis qu'il n'y a pas de zone 3x3 ouverte ?"**
"En labyrinthe parfait, c'est mathématiquement impossible — un arbre couvrant sur 9 cellules a 8 arêtes, mais un 3x3 ouvert en nécessite 12. Pour les labyrinthes imparfaits, je vérifie avant chaque suppression de mur."

**"Comment fonctionne l'encodage hex ?"**
"Chaque cellule a 4 murs encodés sur 4 bits : N=1, E=2, S=4, W=8. Le total donne un chiffre de 0 à F en hexadécimal. Par exemple F = tous les murs, 0 = aucun mur, A = Est+Ouest fermés."

**"Comment tu trouves le plus court chemin ?"**
"J'utilise BFS qui explore les cellules par distance croissante. Le premier chemin trouvé vers la sortie est garanti d'être le plus court."

**"Pourquoi séparer le module mazegen ?"**
"Pour la réutilisabilité. Le module peut être importé dans n'importe quel autre projet via pip install, sans dépendre du script principal ni de la config."
