from pathlib import Path
from src.core.asset_manager import AssetManager,AssetType

class LocalAssetManager(AssetManager):
    def __init__(self, base_path: Path) -> None:
        self.base_path = base_path
        self._check_dirs()

    def _check_dirs(self) -> None:
        for asset_type in AssetType:
            (self.base_path / asset_type.value).mkdir(parents=True, exist_ok=True)

    def _get_path(self, name: str, asset_type: AssetType) -> Path:
        return self.base_path / asset_type.value / name
    
    def save(self, name: str, content: bytes, asset_type: AssetType) -> str:
        path = self._get_path(name, asset_type)
        path.write_bytes(content)
        return f"file://{path.absolute()}"
    
    def get(self, name: str, asset_type: AssetType) -> bytes:
        path = self._get_path(name, asset_type)
        if not path.exists():
            raise FileNotFoundError(f"Asset '{name}' {asset_type.value} not found")
        return path.read_bytes()
    
    def exists(self, name: str, asset_type: AssetType) -> bool:
        path = self._get_path(name, asset_type)
        return path.exists()
    
    def list(self, asset_type: AssetType | None = None) -> list[str]:
        if asset_type:
            path = self.base_path / asset_type.value
            return [f.name for f in path.iterdir() if f.is_file()]
        
        all_files = []
        for at in AssetType:
            all_files.extend(self.list(at))
        return all_files
    
    def delete(self, name: str, asset_type: AssetType) -> None:
        path = self._get_path(name, asset_type)
        path.unlink(missing_ok=True)

    def get_public_url(self, name, asset_type):
        path = self._get_path(name, asset_type)
        return f"file://{path.absolute()}"