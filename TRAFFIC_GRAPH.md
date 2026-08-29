# Traffic Road Network

## Overview

This module loads OpenStreetMap (OSM) road data and converts it into a NetworkX graph for the RouteX traffic and routing system.

The current implementation provides:

- OSM road network loading
- NetworkX graph creation
- Basic road attribute preparation
- Shortest-path calculation
- Routing validation

## Road Network Data

The current test road network is:

```text
data/raw/kothrud_test_area.osm