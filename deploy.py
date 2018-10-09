import os
import json
import subprocess

filename = 'deploy_settings.json'
settings_keys = ('server', 'registry', 'image', 'tag')


def update_settings(settings):
    with open(filename, 'w') as f:
        f.write(json.dumps(settings))


def ask_settings(settings):
    for key in settings_keys:
        if key not in settings or not settings[key]:
            print('{}: '.format(key.capitalize()), end='')
            value = input()
            settings[key] = value
    return settings


def get_settings():
    current_settings = {}
    if os.path.exists(filename):
        with open(filename) as settings:
            try:
                current_settings = json.loads(settings.read())
            except json.decoder.JSONDecodeError:
                pass
    current_settings = ask_settings(current_settings)
    update_settings(current_settings)
    return current_settings


def deploy():
    settings = get_settings()
    server, registry, image, tag = (settings[key] for key in settings_keys)

    def image_name(separator):
        return '{}{}{}'.format(image, separator, tag)

    subprocess.call(['docker', 'build', '-t', image_name(':'), '.'])
    subprocess.call(['docker', 'tag', image_name(':'), '{}/{}'.format(registry, image_name(':'))])
    subprocess.call(['docker', 'push', '{}/{}'.format(registry, image_name(':'))])

    ssh_command = ' && '.join([
        ' '.join(['docker', 'pull', '{}/{}'.format(registry, image_name(':'))]),
        ' '.join(['(docker', 'stop', image_name('_'), '||', 'true)']),
        ' '.join(['(docker', 'rm', image_name('_'), '||', 'true)']),
        'clear',
        ' '.join(['docker', 'run', '-it', '--name', image_name('_'), '{}/{}'.format(registry, image_name(':'))])
    ])
    subprocess.call(['ssh', '-t', 'root@{}'.format(server), ssh_command])


if __name__ == '__main__':
    deploy()
