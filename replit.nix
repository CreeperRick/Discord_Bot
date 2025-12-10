{ pkgs }: {
  deps = [
    pkgs.python39Full
    pkgs.python39Packages.pip
    pkgs.ffmpeg    # optional for music (available in Replit Nix)
  ];
}
