# Communication Container

This container handles device-to-device and device-to-cloud communication for the Clariot platform.

## Responsibilities

- MQTT broker connectivity
- Device discovery
- Message routing between layers
- Protocol translation (if needed)

## Usage

```bash
docker-compose -f Comcontainer/docker-compose.yml up -d
```
