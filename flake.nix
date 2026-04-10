{
  description = "task-tui – Go/Bubble Tea TUI for Taskwarrior";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
  };

  outputs =
    { nixpkgs, ... }:
    let
      inherit (nixpkgs) lib;
      forAllSystems = lib.genAttrs lib.systems.flakeExposed;
    in
    {
      devShells = forAllSystems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in
        {
          default = pkgs.mkShell {
            packages = [
              pkgs.go
              pkgs.gotools
              pkgs.golangci-lint
              pkgs.gopls
            ];

            TASKDATA = "/home/jokeh/projects/task-tui/test_data/";
            TASKRC = "/home/jokeh/projects/task-tui/test_data/taskrc";
          };
        }
      );
    };
}
