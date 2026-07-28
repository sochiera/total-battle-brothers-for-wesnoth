#!/usr/bin/env bash
# G88.1c: buduje kompletny katalog pakietu dystrybucyjnego:
#   <cel>/TotalBattleBrothers.x86_64  (wykonywalne binarium Godota)
#   <cel>/TotalBattleBrothers.pck     (zasoby)
#   <cel>/src/                        (źródła mostu — kandydat BridgeConfig
#                                      „obok wykonywalnego pliku gry")
#
# Użycie: scripts/package.sh <katalog-docelowy>
# Exit 0 wyłącznie przy komplecie; przy błędzie budowy — niezerowy kod, czytelny
# komunikat i brak „udawanego" pakietu (katalog docelowy jest sprzątany).
# Nic nie ląduje w repo: eksport idzie prosto do katalogu docelowego.
set -euo pipefail

# Ścieżki zawsze fizyczne (pwd -P): strażnik „dest poza repo" musi widzieć cel
# po rozwinięciu symlinków, inaczej link spoza drzewa omija porównanie.
real_path() {
    (cd "$1" && pwd -P)
}

ROOT="$(real_path "$(dirname "${BASH_SOURCE[0]}")/..")"
GAME="$ROOT/game"
PRESET="Linux/X11"
BINARY_NAME="TotalBattleBrothers.x86_64"

die() {
    echo "package: BŁĄD: $*" >&2
    exit 1
}

usage() {
    echo "użycie: scripts/package.sh <katalog-docelowy>" >&2
    exit 2
}

[ "$#" -eq 1 ] || usage
DEST_ARG="$1"
[ -n "$DEST_ARG" ] || usage

command -v godot >/dev/null 2>&1 || die "brak polecenia 'godot' w PATH"
[ -f "$GAME/export_presets.cfg" ] || die "brak $GAME/export_presets.cfg"
[ -d "$ROOT/src" ] || die "brak katalogu źródeł $ROOT/src"

mkdir -p "$DEST_ARG"
DEST="$(real_path "$DEST_ARG")"
case "$DEST" in
    "$ROOT"|"$ROOT"/*) die "katalog docelowy musi leżeć poza repo ($ROOT): $DEST" ;;
esac

BINARY="$DEST/$BINARY_NAME"
PCK="${BINARY%.x86_64}.pck"
DESKTOP="$DEST/total-battle-brothers.desktop"

remove_package_artifacts() {
    rm -rf "$BINARY" "$PCK" "$DEST/src" "$DESKTOP"
}

# Artefakty z poprzednich prób nie mogą uchodzić za wynik tej budowy: usuwamy je
# PRZED eksportem, więc każdy sprawdzany dalej plik powstał w tym przebiegu.
remove_package_artifacts

# Godot 4.2.2 potrafi zwrócić exit 0 mimo nieudanego eksportu — o sukcesie
# rozstrzygają artefakty, nie kod wyjścia.
set +e
export_log="$(godot --headless --path "$GAME" --export-release "$PRESET" "$BINARY" 2>&1)"
set -e

fail_export() {
    remove_package_artifacts
    echo "package: BŁĄD: $1" >&2
    echo "--- log eksportu Godota ---" >&2
    echo "$export_log" >&2
    exit 1
}

if [ ! -f "$BINARY" ]; then
    hint=""
    case "$export_log" in
        *"export template"*|*"export_template"*|*"No export template"*)
            hint=" (wygląda na brak szablonów eksportu Godot 4.2.2 pod \
~/.local/share/godot/export_templates/4.2.2.stable/)" ;;
    esac
    fail_export "eksport '$PRESET' nie utworzył binarium $BINARY$hint"
fi
[ -s "$BINARY" ] || fail_export "binarium jest puste: $BINARY"
[ -x "$BINARY" ] || fail_export "binarium nie jest wykonywalne (+x): $BINARY"
[ -s "$PCK" ] || fail_export "eksport nie utworzył niepustego .pck: $PCK"

fail_package() {
    remove_package_artifacts
    die "$1"
}

# Źródła mostu obok binarium (bez śmieci bajtkodu).
rm -rf "$DEST/src"
mkdir -p "$DEST/src"
tar -C "$ROOT/src" --exclude='__pycache__' --exclude='*.pyc' -cf - . \
    | tar -C "$DEST/src" -xf - \
    || fail_package "kopiowanie src/ do $DEST/src nie powiodło się"

[ -d "$DEST/src/tbbbridge" ] || fail_package "pakiet nie zawiera $DEST/src/tbbbridge"

# G88.1g: wpis .desktop obok gry — klik w menedżerze plików bez terminala.
# Exec wskazuje bezwzględną ścieżkę binarium TEGO pakietu (nie miejsca instalacji).
cat > "$DESKTOP" <<EOF
[Desktop Entry]
Type=Application
Name=Total Battle Brothers
Exec="$BINARY"
Terminal=false
Categories=Game;
EOF
chmod +x "$DESKTOP"

echo "package: gotowe — $DEST"
echo "package:   binarium: $BINARY"
echo "package:   pck:      $PCK"
echo "package:   źródła:   $DEST/src"
echo "package:   desktop:  $DESKTOP"
