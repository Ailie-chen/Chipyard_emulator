import socket
import logging
from .wlutil import *

# Kinda hacky (technically not guaranteed to give a free port, just very likely)
def get_free_tcp_port():
	tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	tcp.bind(('', 0))
	addr, port = tcp.getsockname()
	tcp.close()
	return str(port)

# Returns a command string to launch the given config in spike. Must be called with shell=True.
def getSpikeCmd(config, nodisk=False):

    if 'img' in config and not nodisk:
        raise ValueError("Spike does not support disk-based configurations")

    if 'spike' in config:
        spikeBin = str(config['spike'])
    else:
        spikeBin = 'spike'

    cmd = [spikeBin,
           config.get('spike-args', ''),
           ' -p' + str(config['cpus']),
           ' -m' + str( int(config['mem'] / (1024*1024)) )]
    
    if nodisk:
        cmd.append(str(noDiskPath(config['bin'])))
    else:
        cmd.append(str(config['bin']))

    return " ".join(cmd)

# Returns a command string to luanch the given config in qemu. Must be called with shell=True.
def getQemuCmd(config, nodisk=False):
    log = logging.getLogger()

    launch_port = get_free_tcp_port()

    if nodisk:
        exe = str(noDiskPath(config['bin']))
    else:
        exe = str(config['bin'])

    if 'qemu' in config:
        qemuBin = str(config['qemu'])
    else:
        qemuBin = 'qemu-system-riscv64'

    cmd = [qemuBin,
           '-nographic',
           '-bios none',
           '-smp', str(config['cpus']),
           '-machine', 'virt',
           '-m', str( int(config['mem'] / (1024*1024)) ),
           '-kernel', exe,
           '-object', 'rng-random,filename=/dev/urandom,id=rng0',
           '-device', 'virtio-rng-device,rng=rng0',
           '-device', 'virtio-net-device,netdev=usernet',
           '-netdev', 'user,id=usernet,hostfwd=tcp::' + launch_port + '-:22']

    if 'img' in config and not nodisk:
        cmd = cmd + ['-device', 'virtio-blk-device,drive=hd0',
                     '-drive', 'file=' + str(config['img']) + ',format=raw,id=hd0']

    return " ".join(cmd) + " " + config.get('qemu-args', '')

def launchWorkload(baseConfig, jobs=None, spike=False, interactive=True):
    """Launches the specified workload in functional simulation.

    cfgName: unique name of the workload in the cfgs
    cfgs: initialized configuration (contains all possible workloads)
    jobs: List of job names to launch. If jobs is None we use the parent of
    all the jobs (i.e.  the top-level workload in the config).
    spike: Use spike instead of the default qemu as the functional simulator
    interactive: If true, the output from the simulator will be displayed to
        stdout. If false, only the uartlog will be written (it is written live and
        unbuffered so users can still 'tail' the output if they'd like).

    Returns: Path of output directory
    """
    log = logging.getLogger()

    if spike and baseConfig.get('spike', True) is None:
        raise RuntimeError("This workload does not support spike")
    
    if not spike and baseConfig.get('qemu', True) is None:
        raise RuntimeError("This workload does not support qemu")

    if jobs == None:
        configs = [ baseConfig ]
    else:
        configs = [ baseConfig['jobs'][j] for j in jobs ]

    baseResDir = getOpt('res-dir') / getOpt('run-name')
    for config in configs:
        if config['launch']:
            runResDir = baseResDir / config['name']
            uartLog = runResDir / "uartlog"
            os.makedirs(runResDir)

            if spike:
                if 'img' in config and not config['nodisk']:
                    sys.exit("Spike currently does not support disk-based " +
                            "configurations. Please use an initramfs based image.")
                cmd = getSpikeCmd(config, config['nodisk'])
            else:
                cmd = getQemuCmd(config, config['nodisk'])

            log.info("Running: " + "".join(cmd))
            if not interactive:
                log.info("For live output see: " + str(uartLog))
            with open(uartLog, 'wb', buffering=0) as uartF:
                with sp.Popen(cmd.split(), stderr=sp.STDOUT, stdout=sp.PIPE) as p:
                        for c in iter(lambda: p.stdout.read(1), b''):
                            if interactive:
                                sys.stdout.buffer.write(c)
                                sys.stdout.flush()
                            uartF.write(c)

            if 'outputs' in config:
                outputSpec = [ FileSpec(src=f, dst=runResDir) for f in config['outputs']]
                copyImgFiles(config['img'], outputSpec, direction='out')

    if 'post_run_hook' in baseConfig:
        prhCmd = [baseConfig['post_run_hook'].path] + baseConfig['post_run_hook'].args + [baseResDir]
        log.info("Running post_run_hook script: " + ' '.join([ str(x) for x in prhCmd]))
        try:
            run(prhCmd, cwd=config['workdir'])
        except sp.CalledProcessError as e:
            log.info("\nRun output available in: " + str(baseResDir))
            raise RuntimeError("Post run hook failed:\n" + str(e.output))

    return baseResDir
