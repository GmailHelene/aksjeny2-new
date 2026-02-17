#!/bin/bash
set -e

# Install build dependencies
apt-get update
apt-get install -y build-essential wget python3-dev

# NumPy will be installed via requirements.txt to avoid version conflicts

# Download and install TA-Lib from source with retries
for i in {1..3}; do
    if wget --tries=3 --retry-connrefused --waitretry=3 http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz; then
        break
    fi
    if [ $i -eq 3 ]; then
        echo "Failed to download TA-Lib after 3 attempts"
        exit 1
    fi
    sleep 5
done

tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/

# Configure with debugging output
echo "Running configure..."
./configure --prefix=/usr CFLAGS="-fPIC -std=c99" --enable-shared

# Build the library
echo "Running make..."
make -j$(nproc) || make  # Retry without parallel build if it fails

# Clean any previous installs
rm -f /usr/lib/libta_lib* 2>/dev/null || true
rm -rf /usr/include/ta-lib 2>/dev/null || true

echo "Running make install..."
make install

# Verify the installation
echo "Verifying TA-Lib installation..."
if [ ! -f "/usr/lib/libta_lib.so.0" ]; then
    echo "Error: TA-Lib installation failed - library not found"
    exit 1
fi

cd ..

# Show what files were installed
echo "Installed files in /usr/lib:"
ls -l /usr/lib/libta*
echo "Installed files in /usr/include:"
ls -l /usr/include/ta-lib/

cd ..
rm -rf ta-lib-0.4.0-src.tar.gz ta-lib/

# Create ta-lib.conf and update ldconfig
mkdir -p /etc/ld.so.conf.d/
echo "/usr/lib" > /etc/ld.so.conf.d/ta-lib.conf
echo "/usr/local/lib" >> /etc/ld.so.conf.d/ta-lib.conf
ldconfig

# Debug: Show all library paths
echo "Library search paths:"
ldconfig -v 2>/dev/null | grep -v ^$'\t'

# Verify library files exist
echo "Checking for library files..."
if [ ! -f "/usr/lib/libta_lib.so.0" ]; then
    echo "Error: libta_lib.so.0 not found in /usr/lib"
    find /usr -name "libta_lib*" 2>/dev/null || true
    exit 1
fi

# Show found library files
echo "Found library files:"
find /usr -name "libta_lib*" 2>/dev/null

# Ensure proper permissions
chmod 755 /usr/lib/libta_lib.so* 2>/dev/null || true

# Verify library is installed and linkable
echo "Checking library in ldconfig cache..."
ldconfig -p | grep libta || true

# Set environment variables
export TA_INCLUDE_PATH=/usr/include/ta-lib
export TA_LIBRARY_PATH=/usr/lib
export LD_LIBRARY_PATH=/usr/lib:/usr/local/lib:$LD_LIBRARY_PATH

# Verify header files with debug output
echo "Checking for header files..."
if [ -d "/usr/include/ta-lib" ]; then
    echo "Found header files:"
    ls -l /usr/include/ta-lib/
else
    echo "Error: ta-lib headers not found in /usr/include/ta-lib"
    ls -l /usr/include/ta* || true
    exit 1
fi

# Install TA-Lib Python wrapper (deaktivert for Railway build)
# echo "Installing TA-Lib Python wrapper..."
# export LD_LIBRARY_PATH=/usr/lib:$LD_LIBRARY_PATH
#
# # Try to install pre-built wheel first
# pip install --no-cache-dir --only-binary :all: TA-Lib || \
# # If that fails, build from source with specific settings
# LIBRARY_PATH=/usr/lib \
# INCLUDE_PATH=/usr/include \
# C_INCLUDE_PATH=/usr/include/ta-lib \
# CFLAGS="-I/usr/include/ta-lib -fPIC -std=c99" \
# LDFLAGS="-L/usr/lib" \
# pip install --no-cache-dir --no-binary :all: TA-Lib
