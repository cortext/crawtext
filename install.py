import pip
def pip_install(*packages):
    """ Install packages diretly in the shell """
    for name in packages:
        cmd = ['install', name]
        if not hasattr(sys, 'real_prefix'):
            # Si pas dans un virtual env, install juste
            # dans le dossier utilisateur
            cmd.append('--user')
        pip.main(cmd)
with
