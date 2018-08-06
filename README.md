# Pandoc Plugin

This is a plugin for [Janeway](https://github.com/BirkbeckCTP/janeway) that provides a button for typesetters to automatically generate html or xml files from user article submissions in docx/rtf. These files are first converted to markdown, and from there to html or xml, and then registered as galleys of the original article.

## How to install:

(You can find plugin installation instructions in the README for the back_content plugin [here](https://github.com/BirkbeckCTP/back_content))

1. SSH into the server and navigate to: /path/to/janeway/src/plugins
2. Use git to clone the plugin's repository here. For example: `git clone https://github.com/hackman104/pandoc_plugin.git`
3. Make sure you have activated janeway's virtual environment
4. Return to /path/to/janeway/src and run `python manage.py install_plugins`
5. Restart apache (command will depend on your distro)
6. Go to your journal webpage, go to the manager, and click "Plugins" at the bottom of the side-bar on the left
7. Find the plugin you are working on, click its link, and then enable it and click submit

### pandoc

*N. B. You must have pandoc installed on your server to use this plugin. Please see pandoc's installation documentation __[here](https://pandoc.org/installing.html)__.*

Installing pandoc on RHEL was difficult, so here are further instructions:
- If using RHEL, most up-to-date version seems to be 1.12, need at least 1.13 for full docx support, so [build from source](https://pandoc.org/installing.html)
- Pandoc must be available to all users, this is how I accomplished this:
    - Download [most recent pandoc](https://hackage.haskell.org/package/pandoc) tarball to server
    - Unzip: `tar xvzf pandoc-2.2.2.1.tar.gz` (replace version number with whichever you downloaded)
    - Install [stack](https://docs.haskellstack.org/en/stable/install_and_upgrade/): `curl -sSL https://get.haskellstack.org/ | sh`
    - Move into unzipped pandoc diretory, run `stack setup` then `stack install` - installs to ~/.local/bin (will take quite a while)
    - Copy to /opt:
    ```
    sudo mkdir /opt/pandoc
    sudo cp ~/.local/bin/pandoc /opt/pandoc/pandoc
    ```
    - Symlink into /usr/local/bin: `ln -s /opt/pandoc/pandoc /usr/local/bin/pandoc`
    - If something goes wrong and you need to remove the symlink, just type `sudo rm /usr/local/bin/pandoc`
- Pandoc should now be available for all users to run, ensuring the plugin will work
