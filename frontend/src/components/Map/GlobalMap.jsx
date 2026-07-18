import { useEffect, useRef } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import mapData from '../../data/map_data.json'; 

mapboxgl.accessToken = import.meta.env?.VITE_MAPBOX_ACCESS_TOKEN;

const GlobalMap = ({ selectedChokepoints, setSelectedChokepoints }) => {
  const mapContainer = useRef(null);
  const map = useRef(null);

  // --- INITIALIZE MAP ---
  useEffect(() => {
    if (map.current) return;

    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/dark-v11',
      center: [65.0, 20.0], 
      zoom: 3.5 
    });

    map.current.on('load', () => {
      // 1. Refineries Layer
      const refFeatures = mapData.refineries.map(ref => ({
        type: 'Feature',
        geometry: { type: 'Point', coordinates: ref.coords },
        properties: { name: ref.id }
      }));

      map.current.addSource('refineries', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: refFeatures }
      });
      map.current.addLayer({
        id: 'refinery-points',
        type: 'circle',
        source: 'refineries',
        paint: { 'circle-radius': 6, 'circle-color': '#00ff00' }
      });

      // 2. Suppliers Layer
      const supplierFeatures = mapData.suppliers.map(sup => ({
        type: 'Feature',
        geometry: { type: 'Point', coordinates: sup.coords },
        properties: { name: sup.id, label: sup.name }
      }));

      map.current.addSource('suppliers', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: supplierFeatures }
      });
      map.current.addLayer({
        id: 'supplier-points',
        type: 'circle',
        source: 'suppliers',
        paint: {
          'circle-radius': 7,
          'circle-color': '#3399ff',
          'circle-stroke-width': 2,
          'circle-stroke-color': '#ffffff'
        }
      });

      // 3. Chokepoints Source
      const chokeFeatures = mapData.chokepoints.map(cp => ({
        type: 'Feature',
        geometry: { type: 'Point', coordinates: cp.coords },
        properties: { name: cp.id }
      }));

      map.current.addSource('chokepoints', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: chokeFeatures }
      });

      // Base Chokepoint Layer (Red)
      map.current.addLayer({
        id: 'chokepoint-points-unselected',
        type: 'circle',
        source: 'chokepoints',
        paint: { 
            'circle-radius': 10, 'circle-color': '#ff0000',
            'circle-stroke-width': 2, 'circle-stroke-color': '#ffffff'
        } 
      });

      // Highlighted Chokepoint Layer (Yellow)
      map.current.addLayer({
        id: 'chokepoint-points-selected',
        type: 'circle',
        source: 'chokepoints',
        filter: ['in', 'name', ''], 
        paint: { 
            'circle-radius': 14, 'circle-color': '#ffaa00',
            'circle-stroke-width': 3, 'circle-stroke-color': '#ffffff'
        } 
      });

      // 4. Click Logic connecting directly to React State
      map.current.on('click', 'chokepoint-points-unselected', (e) => {
        const cpName = e.features[0].properties.name;
        setSelectedChokepoints(prev => {
            if (prev.includes(cpName)) return prev.filter(c => c !== cpName);
            return [...prev, cpName];
        });
      });

      map.current.on('mouseenter', 'chokepoint-points-unselected', () => map.current.getCanvas().style.cursor = 'pointer');
      map.current.on('mouseleave', 'chokepoint-points-unselected', () => map.current.getCanvas().style.cursor = '');

      // 5. Hover Popups for all node types (refineries, suppliers, chokepoints)
      const hoverPopup = new mapboxgl.Popup({ closeButton: false, closeOnClick: false, offset: 12 });
      const bindHoverPopup = (layerId, labelFn) => {
        map.current.on('mouseenter', layerId, (e) => {
          map.current.getCanvas().style.cursor = 'pointer';
          const feature = e.features[0];
          hoverPopup
            .setLngLat(feature.geometry.coordinates)
            .setHTML(`<strong>${labelFn(feature.properties)}</strong>`)
            .addTo(map.current);
        });
        map.current.on('mouseleave', layerId, () => {
          map.current.getCanvas().style.cursor = '';
          hoverPopup.remove();
        });
      };

      bindHoverPopup('refinery-points', (props) => props.name.replace(/_/g, ' '));
      bindHoverPopup('supplier-points', (props) => props.label || props.name.replace(/_/g, ' '));
      bindHoverPopup('chokepoint-points-unselected', (props) => props.name.replace(/_/g, ' '));
    });
  }, [setSelectedChokepoints]);

  // --- SYNC MAPBOX WITH REACT STATE ---
  // If a user clicks the "Reset" button on the HUD, this clears the yellow dots.
  useEffect(() => {
    if (!map.current || !map.current.isStyleLoaded()) return;
    
    // Fallback to empty string if array is empty so Mapbox doesn't crash
    const filterArray = selectedChokepoints.length > 0 ? selectedChokepoints : [''];
    map.current.setFilter('chokepoint-points-selected', ['in', 'name', ...filterArray]);
  }, [selectedChokepoints]);

  return (
    <div style={{ position: 'relative', height: '100%', width: '100%' }}>
      <div ref={mapContainer} style={{ height: '100%', width: '100%' }} />
      <div className="map-legend">
        <div className="map-legend-item"><span className="legend-dot refinery-dot" />Refinery</div>
        <div className="map-legend-item"><span className="legend-dot supplier-dot" />Supplier</div>
        <div className="map-legend-item"><span className="legend-dot chokepoint-dot" />Chokepoint</div>
      </div>
    </div>
  );
};

export default GlobalMap;