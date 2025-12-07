{
  description = "Develop Python on Nix with uv";

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
      packages = forAllSystems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          pythonPackages = pkgs.python314Packages.override {
            overrides = final: prev: {
              pydantic-core = prev.pydantic-core.overrideAttrs (old: {
                env = (old.env or { }) // {
                  PYO3_USE_ABI3_FORWARD_COMPATIBILITY = "1";
                };
              });
            };
          };
        in
        {
          default = pythonPackages.buildPythonApplication {
            pname = "task-tui";
            version = "0.1.0";
            src = ./.;
            pyproject = true;

            build-system = [
              pythonPackages.hatchling
            ];

            propagatedBuildInputs = with pythonPackages; [
              pydantic
              rich
              textual
              typer
            ];
          };
        }
      );

      devShells = forAllSystems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in
        {
          default = pkgs.mkShell {
            packages = [
              pkgs.python314
              pkgs.uv
            ];

            shellHook = ''
              unset PYTHONPATH
              uv sync
              . .venv/bin/activate
            '';

            TASKDATA = "./test_data/";
            TASKRC = "./test_data/taskrc";
          };
        }
      );
    };
}
