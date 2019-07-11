{ pkgs ? import <nixpkgs> {} }:

with pkgs;

stdenv.mkDerivation {
  name = "sbot-dev-env";
  buildInputs = [
    gnumake
    python3
    python3Packages.poetry
  ];
  LD_LIBRARY_PATH = [ "${libusb1}/lib" ];
}
