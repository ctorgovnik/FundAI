{
  description = "FundAI — Fund OS + AI portfolio manager";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in {
        devShells.default = pkgs.mkShell {
          name = "fundai";

          packages = with pkgs; [
            # C / C++
            cmake
            ninja
            clang
            clang-tools   # clangd, clang-format, clang-tidy
            boost

            # Python
            python312
            python312Packages.pip

            # Utilities
            git
            just          # command runner (optional, for a justfile)
          ];

          shellHook = ''
            export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
            echo "FundAI dev shell"
            echo "  cmake -B build -G Ninja -DCMAKE_BUILD_TYPE=Debug"
            echo "  cmake --build build"
            echo "  ctest --test-dir build -V"
          '';
        };
      });
}
