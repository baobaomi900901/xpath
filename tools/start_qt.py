"""Build and run isolated Qt SDK variants. Runtime launching uses only stdlib."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
QT_ROOT = REPO_ROOT / 'QT'
VERSIONS = json.loads((QT_ROOT / 'versions.json').read_text(encoding='utf-8'))
FRONTENDS = {'widgets': 'qt-widgets-range.exe', 'quick': 'qt-quick-range.exe',
             'profile': 'acc-hidden-profile.exe'}


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description='Qt 5.15 / 6.8 多版本 RPA 靶场')
    parser.add_argument('--versions', nargs='+', choices=VERSIONS)
    parser.add_argument('--frontends', nargs='+', choices=FRONTENDS, default=['widgets', 'quick'])
    parser.add_argument('--form-mode', choices=['grouped', 'flat', 'random'], default='grouped',
                        help='只影响 Widgets；Quick 保持固定表单')
    parser.add_argument('--sdk-root', type=Path, help='Qt 安装根目录，包含版本目录和 Tools')
    parser.add_argument('--qt-root', type=Path, help='单版本 Qt kit 目录（兼容旧 build.ps1）')
    parser.add_argument('--mingw-bin', type=Path, help='单版本 MinGW bin 目录')
    parser.add_argument('--install-sdk', action='store_true', help='缺少 SDK 时使用 aqtinstall 下载；需先安装 aqtinstall')
    parser.add_argument('--skip-build', action='store_true')
    parser.add_argument('--no-launch', action='store_true', help='检查发行文件，不打开窗口')
    parser.add_argument('--self-test', action='store_true', help='运行发行目录的 QtTest 和两套 UI 启动检查，随后退出')
    parser.add_argument('--configuration', choices=['Release'], default='Release')
    args = parser.parse_args(argv)
    if (args.qt_root or args.mingw_bin) and (not args.versions or len(args.versions) != 1):
        parser.error('--qt-root / --mingw-bin 需要 --versions 指定一个版本')
    return args


def runtime_environment():
    env = os.environ.copy()
    for key in ('QT_PLUGIN_PATH', 'QML2_IMPORT_PATH', 'QML_IMPORT_PATH',
                'QT_QPA_PLATFORM_PLUGIN_PATH', 'QT_QPA_PLATFORM', 'QT_QUICK_CONTROLS_STYLE',
                'QML_DISABLE_DISK_CACHE'):
        env.pop(key, None)
    return env


def executable_path(version, frontend):
    return QT_ROOT / 'dist' / version / FRONTENDS[frontend]


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def validate_artifact(version, frontend):
    exe = executable_path(version, frontend)
    folder = exe.parent
    manifest_path = folder / 'manifest.json'
    if not manifest_path.is_file():
        raise FileNotFoundError(f'缺少 {manifest_path}，请先构建 Qt {version}。')
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if manifest.get('qt_version') != version:
        raise ValueError(f'Qt 版本不匹配: {manifest_path}')
    required = [FRONTENDS[frontend], f'Qt{VERSIONS[version]["major"]}Core.dll', 'platforms/qwindows.dll']
    for name in dict.fromkeys(required + list(manifest.get('files', {}))):
        path = folder / name
        if not path.is_file():
            raise FileNotFoundError(f'缺少运行依赖: {path}')
        if manifest.get('files', {}).get(name) != sha256(path):
            raise ValueError(f'发行文件校验失败: {path}；请重新构建。')
    if frontend in ('quick', 'profile') and not (folder / 'qml' / 'QtQuick').is_dir() and not (folder / 'QtQuick.2').is_dir():
        raise FileNotFoundError(f'缺少 QML 运行模块: {folder}')
    return exe


def select_versions():
    # Reuse the existing Win32 key reader, with this range's own selector state.
    try:
        from tools import start_win32 as terminal
    except ImportError:
        import start_win32 as terminal
    if not sys.stdin.isatty():
        return ['5.15.2', '6.8.3']
    options = list(VERSIONS)
    selected = set(options)
    focus = 0
    terminal.configure_output()
    terminal.clear_screen()
    while True:
        lines = ['选择 Qt 版本（方向键移动，空格/Enter 勾选，Esc 取消）', '']
        for index, version in enumerate(options):
            lines.append(f'{">" if focus == index else " "} [{"✓" if version in selected else " "}] Qt {version}')
        lines.append(f'{">" if focus == len(options) else " "} [ 已完成选择 ]')
        print('\x1b[H' + '\n'.join('\x1b[2K' + line for line in lines), flush=True)
        key = terminal.read_key()
        if key == 'up': focus = (focus - 1) % (len(options) + 1)
        elif key == 'down': focus = (focus + 1) % (len(options) + 1)
        elif key in ('space', 'enter') and focus < len(options):
            version = options[focus]
            selected.symmetric_difference_update([version])
        elif key == 'enter' and selected:
            return [version for version in options if version in selected]
        elif key == 'escape': return []
        elif key == 'interrupt': raise KeyboardInterrupt


def find_toolchain(version, args):
    spec = VERSIONS[version]
    roots = [args.sdk_root] if args.sdk_root else [QT_ROOT / '.tools', Path(os.environ.get('QT_SDK_ROOT', 'D:/Qt'))]
    for root in roots:
        kit = args.qt_root or root / version / spec['kit']
        compiler = args.mingw_bin or root / 'Tools' / spec['compiler'] / 'bin'
        if (kit / 'bin/qmake.exe').is_file() and (compiler / 'g++.exe').is_file():
            env = runtime_environment()
            env['PATH'] = os.pathsep.join([str(compiler), str(kit / 'bin'), env.get('PATH', '')])
            actual = subprocess.check_output([str(kit / 'bin/qmake.exe'), '-query', 'QT_VERSION'], text=True, env=env).strip()
            if actual != version:
                raise ValueError(f'指定 Qt {version}，实际 SDK 为 {actual}: {kit}')
            return kit.resolve(), compiler.resolve()
    if args.install_sdk:
        root = roots[0]
        archives = ['qtbase', 'qtdeclarative', 'qtsvg', 'qttools']
        if spec['major'] == 5:
            archives += ['qtquickcontrols', 'qtquickcontrols2', 'qtgraphicaleffects', 'qtimageformats']
        subprocess.run([sys.executable, '-m', 'aqt', 'install-qt', 'windows', 'desktop', version,
                        spec['arch'], '-O', str(root), '--archives', *archives], check=True)
        subprocess.run([sys.executable, '-m', 'aqt', 'install-tool', 'windows', 'desktop', spec['tool'],
                        spec['tool_package'], '-O', str(root)], check=True)
        args.install_sdk = False
        try:
            return find_toolchain(version, args)
        finally:
            args.install_sdk = True
    raise FileNotFoundError(f'未找到 Qt {version} 和匹配 MinGW。设置 --sdk-root，或安装 aqtinstall 后加 --install-sdk。')


def build(version, args):
    kit, compiler = find_toolchain(version, args)
    env = runtime_environment()
    ninja = shutil.which('ninja')
    if not ninja:
        for candidate in (QT_ROOT / '.tools/Tools/Ninja/ninja.exe', Path('D:/Qt/Tools/Ninja/ninja.exe')):
            if candidate.is_file(): ninja = str(candidate); break
    if not ninja: raise FileNotFoundError('需要 CMake 和 Ninja（将 ninja.exe 加入 PATH）。')
    env['PATH'] = os.pathsep.join([str(compiler), str(kit / 'bin'), str(Path(ninja).parent), env.get('PATH', '')])
    folder = QT_ROOT / 'build' / version
    deploy = QT_ROOT / 'dist' / version
    deploy.mkdir(parents=True, exist_ok=True)
    # Invalidate any previous success marker before changing the deployment.
    (deploy / 'manifest.json').unlink(missing_ok=True)
    subprocess.run(['cmake', '-S', str(QT_ROOT), '-B', str(folder), '-G', 'Ninja',
                    '-DCMAKE_BUILD_TYPE=Release', f'-DCMAKE_MAKE_PROGRAM={ninja}',
                    f'-DCMAKE_PREFIX_PATH={kit}', f'-DQT_DIR={kit}/lib/cmake/Qt{VERSIONS[version]["major"]}',
                    f'-DCMAKE_CXX_COMPILER={compiler / "g++.exe"}'], env=env, check=True)
    subprocess.run(['cmake', '--build', str(folder), '--parallel', '6'], env=env, check=True)
    subprocess.run(['ctest', '--test-dir', str(folder), '--output-on-failure'], env=env, check=True)
    for filename in [*FRONTENDS.values(), 'qt-range-tests.exe']:
        shutil.copy2(folder / filename, deploy / filename)
    deploy_args = [str(kit / 'bin/windeployqt.exe'), '--release', '--compiler-runtime', '--no-translations', '--verbose', '0']
    if VERSIONS[version]['major'] == 5:
        # Some MinGW 8.1 distributions retain PE debug sections in release
        # plugins. Qt 5 windeployqt misclassifies them and refuses qwindows.
        # Use this exact kit's runtime/module/plugin trees instead; the
        # isolated runtime test validates their ABI and completeness.
        for dll in (kit / 'bin').glob('*.dll'):
            shutil.copy2(dll, deploy / dll.name)
        for name in ('libgcc_s_seh-1.dll', 'libstdc++-6.dll', 'libwinpthread-1.dll'):
            shutil.copy2(compiler / name, deploy / name)
        for plugin in ('platforms', 'imageformats', 'iconengines', 'styles'):
            shutil.copytree(kit / 'plugins' / plugin, deploy / plugin, dirs_exist_ok=True)
        shutil.copytree(kit / 'qml', deploy / 'qml', dirs_exist_ok=True)
    else:
        deploy_args += ['--qmldir', str(QT_ROOT / 'qml')]
        subprocess.run(deploy_args + ['--dir', str(deploy),
                        *[str(deploy / name) for name in [*FRONTENDS.values(), 'qt-range-tests.exe']]], env=env, check=True)
    # Support the deployer's qml/ layout as well as older flat layouts.
    qml_path = 'qml' if (deploy / 'qml').is_dir() else '.'
    (deploy / 'qt.conf').write_text(f'[Paths]\nPrefix=.\nPlugins=.\nQml2Imports={qml_path}\n', encoding='utf-8')
    files = {path.relative_to(deploy).as_posix(): sha256(path) for path in deploy.rglob('*') if path.is_file()}
    (deploy / 'manifest.json').write_text(json.dumps({'qt_version': version, 'architecture': 'x64',
        'kit': str(kit), 'files': files}, ensure_ascii=False, indent=2), encoding='utf-8')


def self_test(version):
    folder = QT_ROOT / 'dist' / version
    env = runtime_environment()
    # Prove the deployed application does not depend on SDK/toolchain PATH.
    env['PATH'] = os.pathsep.join([os.path.join(os.environ.get('SystemRoot', 'C:/Windows'), 'System32'),
                                 os.environ.get('SystemRoot', 'C:/Windows')])
    screenshots = QT_ROOT / 'verify/artifacts'
    screenshots.mkdir(parents=True, exist_ok=True)
    subprocess.run([str(folder / 'qt-range-tests.exe'), '-o', str(screenshots / f'{version}-tests.xml') + ',xml'],
                   cwd=folder, env=env, check=True, timeout=90)
    for frontend in ('widgets', 'quick'):
        for page in range(3):
            suffix = '' if page == 0 else f'-page{page}'
            subprocess.run([str(validate_artifact(version, frontend)), '--smoke-test', '--page', str(page), '--screenshot',
                            str(screenshots / f'{version}-{frontend}{suffix}.png')], cwd=folder, env=env, check=True, timeout=30)
    subprocess.run([str(validate_artifact(version, 'profile')), '--smoke-test', '--screenshot',
                    str(screenshots / f'{version}-profile.png')], cwd=folder, env=env, check=True, timeout=30)


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'): stream.reconfigure(encoding='utf-8', errors='replace')
    args = parse_args(argv)
    versions = list(dict.fromkeys(args.versions or select_versions()))
    if not versions: return 0
    try:
        for version in versions:
            if not args.skip_build: build(version, args)
            for frontend in dict.fromkeys(args.frontends): validate_artifact(version, frontend)
            if args.self_test: self_test(version)
        if args.no_launch or args.self_test:
            print('Qt 产物检查完成: ' + ', '.join(versions)); return 0
        for version in versions:
            for frontend in dict.fromkeys(args.frontends):
                exe = executable_path(version, frontend)
                command = [str(exe)]
                if frontend == 'widgets': command += ['--form-mode', args.form_mode]
                process = subprocess.Popen(command, cwd=exe.parent, env=runtime_environment(),
                                           creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                try:
                    code = process.wait(timeout=1)
                    raise RuntimeError(f'{exe.name} 启动后退出: {code}')
                except subprocess.TimeoutExpired:
                    print(f'已启动 Qt {version} / {frontend}，PID={process.pid}')
        return 0
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(f'错误: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
