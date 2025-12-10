# Docu-PDF

A comprehensive document processing and PDF generation application built with Streamlit. This application allows users to create, edit, and manage multi-page documents with support for various file types including images, SVGs, JSON wall data, and CSV tables.

## Features

- **Multi-page document management**: Create and manage documents with multiple pages
- **File upload support**: Upload images (SVG, PNG, JPG), JSON wall data, and CSV tables
- **Wall projection visualization**: Generate SVG projections from wall data
- **PDF generation**: Convert documents to PDF format with custom styling
- **Redis integration**: Optional Redis backend for asset storage and management
- **Responsive UI**: Streamlit-based interface with editing capabilities
- **Template engine**: Flexible template system for document rendering

## Prerequisites

- Python 3.8 or higher
- Redis server (optional, for asset storage backend)

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/docu-pdf.git
cd docu-pdf
```

### 2. Set up a virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

This project uses uv for dependency management. First, install uv if you don't have it:

```bash
pip install uv
```

Then install the project dependencies:

```bash
uv sync
```

Alternatively, you can use pip with the pyproject.toml file:

```bash
pip install -e .
```

### 4. Install Node.js dependencies (for SCSS compilation)

Make sure you have Node.js and npm installed, then run:

```bash
npm install
```

### 5. Compile SCSS styles

```bash
npm run build:scss
```

### 6. Start Redis server (optional)

If you want to use Redis for asset storage:

```bash
# Install Redis (Ubuntu/Debian)
sudo apt install redis-server

# Or on macOS
brew install redis

# Start Redis server
redis-server
```

## Usage
### Running the application

If you're using uv for dependency management:

```bash
uv run streamlit run src/streamlit/app.py
```

Or if you've installed dependencies in a virtual environment:

```bash
streamlit run src/streamlit/app.py
```


The application will start and be accessible at `http://localhost:8501` by default.

### Development workflow

To work with styles, you can use the watch command to automatically compile SCSS changes:

```bash
npm run build:scss:watch
```

## Streamlit Configuration

The application includes a `.streamlit/config.toml` file that configures the Streamlit interface with:

- Server settings: static file serving

This project includes several helpful commands defined in `pyproject.toml`:

- `uv run dev` - Start the Streamlit application
- `uv run build-scss` - Compile SCSS to CSS
- `uv run build-scss-watch` - Watch and compile SCSS files automatically
- `uv run analyze` - Run data analysis script
- `uv run calibrate` - Run calibration script
- `uv run test` - Run tests with pytest
- `uv run test-perf` - Run performance benchmarks

## Project Structure

```
docu-pdf/
├── src/
│   ├── core/                 # Core application logic
│   ├── models/               # Data models and schemas
│   ├── geom_utils/           # Geometry calculation utilities
│   ├── pdf/                  # PDF generation services
│   ├── render/               # Template rendering engine
│   ├── store/                # Storage backends (Redis, etc.)
│   ├── streamlit/            # Streamlit application components
│   ├── svg/                  # SVG processing utilities
│   ├── styles/               # SCSS styles and CSS
│   └── templates/            # HTML templates
├── assets/                   # Static assets
├── temp_assets/              # Temporary asset storage
├── src/streamlit/static/     # Static files for Streamlit
├── README.md                 # This file
├── package.json              # Node.js dependencies and scripts
├── pyproject.toml            # Python project configuration
└── uv.lock                   # Dependency lock file
```

## Configuration

The application uses several configuration parameters:

- **Redis URL**: By default, the application tries to connect to `redis://localhost:6379`
- **Asset storage**: Falls back to local storage if Redis is unavailable
- **Template paths**: Configured in the application code
- **CSS styling**: Managed through SCSS files in `src/styles/scss/`

## Building for Production

### 1. Compile styles

```bash
npm run build:scss
```

### 2. Ensure all dependencies are installed

Using uv (recommended):
```bash
uv sync
```

Or with pip:
```bash
pip install -e .
```
### 3. Run the application

```bash
streamlit run src/streamlit/app.py --server.port 8080
```

The application behavior can be customized using the configuration in `.streamlit/config.toml`, which includes settings for:
- Server: static file serving and auto-reload on save
- Client: toolbar appearance
- UI: hiding the top bar for a cleaner interface

These settings can be overridden by environment variables or command-line arguments when running Streamlit.


## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add documentation for new features
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Dependencies

This project uses several key dependencies:

- **Streamlit**: Web framework for the UI
- **Pydantic**: Data validation and settings management
- **Redis**: Optional backend for asset storage
- **WeasyPrint**: PDF generation from HTML/CSS
- **Shapely**: Geometric operations
- **NumPy**: Mathematical computations
- **Pandas**: Data manipulation
- **lxml**: XML/SVG processing

## Troubleshooting

### Common issues:

1. **Redis connection errors**: The application will automatically fall back to local storage if Redis is unavailable.

2. **SCSS compilation errors**: Make sure Node.js and npm are properly installed, then run:
   ```bash
   npm install
   npm run build:scss
   ```
3. **Missing dependencies**: If you encounter import errors, make sure all dependencies are installed:
   ```bash
   # Using uv (recommended)
   uv sync
   
   # Or using pip
   pip install -e .
   ```

4. **Streamlit not found**: Install Streamlit:
   ```bash
   # Using uv
   uv pip install streamlit
   
   # Or using pip
   pip install streamlit
   ```

5. **uv not found**: Install uv:
   ```bash
   pip install uv
   ```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Streamlit for the web framework
- The open-source libraries that made this project possible
