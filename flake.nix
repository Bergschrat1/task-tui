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
      # Go settings
      goVersion = 23;
    in
    {
      packages = forAllSystems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          pythonPackages = pkgs.python313Packages;
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

            runtimeDependencies = [ pkgs.taskwarrior3 ];
          };
        }
      );
      overlays.default = final: prev: {
          go = final."go_1_${toString goVersion}";
        };


      devShells = forAllSystems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in
        {
          default = pkgs.mkShell {
            packages = [
              pkgs.python313
              pkgs.uv
              # go (version is specified by overlay)
              pkgs.go
              # goimports, godoc, etc.
              pkgs.gotools
              # https://github.com/golangci/golangci-lint
              pkgs.golangci-lint
              # lsp
              pkgs.gopls
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
