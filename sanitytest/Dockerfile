# Use the UBI 9 micro image as base
FROM registry.access.redhat.com/ubi9/python-39

# Set the working directory in the container
WORKDIR /app

# Copy the Python script into the container
COPY sanitytest_containerversion.py /app/

# Install the required Python packages
RUN pip install kubernetes

# Run the Python script when the container starts
CMD ["python", "/app/sanitytest_containerversion.py"]
