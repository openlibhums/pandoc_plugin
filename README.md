# Pandoc Plugin

This is a plugin for [Janeway](https://github.com/BirkbeckCTP/janeway) that provides a button for typesetters to automatically generate html files from user article submissions in docx/rtf. These files are first converted to markdown, and from there to html, and then registered as galleys of the original article.

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

Most of the package managers for Linux distributions offer older versions of Pandoc, and you need at least 1.13 for full docx support. Luckily, pandoc offers a compiled distribution in .deb format:

``` sh
wget 'https://github.com/jgm/pandoc/releases/download/2.19.2/pandoc-2.19.2-1-amd64.deb'
dpkg -i pandoc-2.5-1-amd64.deb
rm pandoc-2.5-1-amd64.deb
```
Pandoc should now be available for all users to run, ensuring the plugin will work
