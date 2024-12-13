
# Pandoc Plugin for Janeway

This plugin integrates [Pandoc](https://pandoc.org/) into the Janeway platform, enabling document conversion for articles. It supports generating HTML and PDF files from manuscripts and adding optional stamped coversheets.

## Features

- Converts Word documents (`.docx`) and RTF manuscripts into Markdown, HTML, and optionally PDF format.
- Automatically registers the generated HTML as galleys for the original article.
- Optional inclusion of custom coversheets for PDF generation.

## How to Install

1. SSH into the server and navigate to the plugins directory:
   ```bash
   cd /path/to/janeway/src/plugins
   ```

2. Use git to clone the plugin repository:
   ```bash
   git clone https://github.com/openlibhums/pandoc_plugin.git
   ```

3. Activate Janeway's virtual environment:
   ```bash
   source /path/to/janeway/venv/bin/activate
   ```

4. Return to the Janeway source directory and install the plugin:
   ```bash
   cd /path/to/janeway/src
   pip3 install -r plugins/pandoc_plugin/requirements.txt
   python manage.py install_plugins pandoc_plugin
   ```

5. Restart your webserver to apply the changes (command depends on your distro).

6. Log in to your journal's admin interface:
   - Go to the "Manager" section.
   - Click "Plugins" at the bottom of the left-hand sidebar.
   - Locate the Pandoc Plugin, enable it, and click submit.

### Installing Pandoc and XeLaTeX

#### Pandoc

You must have Pandoc installed on your server to use this plugin. Most Linux distributions include older versions of Pandoc, but at least version 1.13 is required for full `.docx` support.

To install a newer version of Pandoc:

```bash
wget 'https://github.com/jgm/pandoc/releases/download/2.19.2/pandoc-2.19.2-1-amd64.deb'
dpkg -i pandoc-2.19.2-1-amd64.deb
rm pandoc-2.19.2-1-amd64.deb
```

Verify that Pandoc is installed and available:
```bash
pandoc --version
```

#### XeLaTeX

The plugin uses `xelatex` as the PDF engine. If you encounter the error `xelatex not found`, follow these steps to install `xelatex` on your system.

##### On Ubuntu/Debian:
To install `xelatex` using the TeX Live distribution:
```bash
sudo apt update
sudo apt install texlive-xetex
```

##### On CentOS/RHEL:
```bash
sudo yum install texlive-xetex
```

##### On macOS:
```bash
brew install --cask mactex
```

Verify `xelatex` is installed:
```bash
xelatex --version
```

## Configuration

### Settings

The plugin provides the following configurable settings:

1. **Coversheet HTML (`cover_sheet`)**:
   - Specifies the HTML template used for the stamped coversheet.
   - Configured via the plugin manager interface.

2. **Extract Images**:
   - Boolean setting to enable extraction of images.
   - Configured via the plugin manager interface.


### Updating Settings

1. Go to the Janeway admin panel.
2. Navigate to `Settings > Plugins > Pandoc Plugin`.
3. Configure the above settings as needed.

## Usage

### Generating Files via Management Command

To generate HTML or PDFs for specific articles or files, use the management command:

```bash
python manage.py generate_pdfs <article_id> --owner <email> --conversion_type stamped or unstamped
```

- `article_id`: ID of the article to process.
- `--owner`: Email of the account owner for the generated file.
- `--conversion_type`: Tells Janeway whether to add a cover sheet to the converted file.

#### Example Command:

```bash
python manage.py generate_pdfs 123 456 --owner=editor@example.com
```

### File Generation in the User Interface

- Editors can trigger HTML and PDF generation from the Janeway interface for individual files in typesetting by clicking the "Options" link

## License

This plugin is licensed under the [GNU Affero General Public License](https://www.gnu.org/licenses/agpl-3.0.en.html) (AGPLv3).
