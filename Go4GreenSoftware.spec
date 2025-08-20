# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files

# Automatically collect data files from specific packages (ultralytics, yapf_third_party, etc.)
ultralytics_datas = collect_data_files('ultralytics')
yapf_datas = collect_data_files('yapf_third_party')
dino_datas = collect_data_files('groundingdino')
torch_datas = collect_data_files('torch')

a = Analysis(
    ['GUI.py'],
    pathex=[],
    binaries=[],
    datas=[('ObjectDetection', 'ObjectDetection'), ('output', 'output'), 
    ('azureChaleur.py', 'azureChaleur.py'), ('azureElec.py', 'azureElec.py'), 
    ('azureHeures.py', 'azureHeures.py'), ('all_images', 'all_images'), 
    ('cropped_images', 'cropped_images'), ('temp_images', 'temp_images'), 
    ('cloudChaleur.py', 'cloudChaleur.py'), ('cloudElec.py', 'cloudElec.py'), 
    ('credential.json', 'credential.json'), ('dinoTest.py', 'dinoTest.py'),
    ('credentialBackup.json', 'credentialBackup.json'), 
    ('go4green-435412-6555fb2e2af1.json', 'go4green-435412-6555fb2e2af1.json'), 
    ('groundingdino_swint_ogc.pth', 'groundingdino_swint_ogc.pth'), ('utils.py', 'utils.py'),
    ('Forest-ttk-theme-master', 'Forest-ttk-theme-master'),
    ('mainTer.py', 'mainTer.py'),
    ('go4greenfr_logo.ico', 'go4greenfr_logo.ico'),('GroundingDINO_SwinT_OGC.py', 'GroundingDINO_SwinT_OGC.py')
    ]+ultralytics_datas+yapf_datas + dino_datas + torch_datas,
    hiddenimports=[
    'msrest.authentication',
    'azure.cognitiveservices.vision.computervision',
    'azure.cognitiveservices.vision.computervision.models',
    'cv2',
    'google.cloud.vision',
    'google.cloud.vision_v1.types',
    'groundingdino.util.inference',
    'ultralytics',
    'dropbox',
    'groundingdino',
    'yapf'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Go4GreenSoftware',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
