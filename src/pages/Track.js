import React, { useState, useEffect, useRef } from "react";
import {
  Box,
  Typography,
  Paper,
  Card,
  CardContent,
  Chip,
  LinearProgress,
  Alert,
  Button,
  IconButton,
} from "@mui/material";
import { Close, LocalShipping, CheckCircle } from "@mui/icons-material";
import { useLocation, useNavigate } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import TopNavBar from "../components/TopNavBar";
import { dispatchAPI, ambulanceAPI } from "../services/api";

const Track = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { emergencyData } = location.state || {};

  const [mobileOpen, setMobileOpen] = useState(false);
  const [ambulanceRoutes, setAmbulanceRoutes] = useState([]);
  const [selectedAmbulance, setSelectedAmbulance] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(true);
  const [countdown, setCountdown] = useState(5);
  const [isDispatching, setIsDispatching] = useState(false);
  const [trackMap, setTrackMap] = useState(null);
  const mapInitialized = useRef(false);

  useEffect(() => {
    if (!emergencyData) {
      navigate("/active-emergencies");
      return;
    }

    // Calculate routes
    calculateRoutes();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [emergencyData]);

  useEffect(() => {
    if (ambulanceRoutes.length > 0 && !mapInitialized.current) {
      initializeMap();
      mapInitialized.current = true;
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ambulanceRoutes]);

  useEffect(() => {
    if (!isAnalyzing && countdown > 0) {
      const timer = setTimeout(() => {
        setCountdown(countdown - 1);
      }, 1000);
      return () => clearTimeout(timer);
    } else if (countdown === 0 && !isDispatching) {
      handleAutoDispatch();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [countdown, isAnalyzing]);

  const calculateRoutes = () => {
    // Simulate calculating routes from 5 available ambulances
    const patientLocation = { lat: 28.62, lng: 77.21 };

    const mockAmbulances = [
      { id: "AMB-105", lat: 28.635, lng: 77.225, crew: 4, status: "available" },
      { id: "AMB-208", lat: 28.61, lng: 77.195, crew: 3, status: "available" },
      { id: "AMB-312", lat: 28.64, lng: 77.23, crew: 4, status: "available" },
      { id: "AMB-456", lat: 28.605, lng: 77.215, crew: 2, status: "available" },
      { id: "AMB-589", lat: 28.628, lng: 77.218, crew: 3, status: "available" },
    ];

    const routeColors = ["#FF1744", "#FF6D00", "#FFD600", "#00E676", "#2979FF"];

    const routes = mockAmbulances.map((ambulance, index) => {
      const distance =
        Math.sqrt(
          Math.pow(ambulance.lat - patientLocation.lat, 2) +
            Math.pow(ambulance.lng - patientLocation.lng, 2)
        ) * 100;

      const eta = Math.ceil(distance * 2);

      return {
        ambulanceId: ambulance.id,
        location: { lat: ambulance.lat, lng: ambulance.lng },
        distance: distance.toFixed(2),
        eta: eta,
        crew: ambulance.crew,
        color: routeColors[index],
        path: [
          [ambulance.lng, ambulance.lat],
          [patientLocation.lng, patientLocation.lat],
        ],
      };
    });

    // Sort by ETA
    routes.sort((a, b) => a.eta - b.eta);

    setAmbulanceRoutes(routes);

    // Simulate AI analysis
    setTimeout(() => {
      setSelectedAmbulance(routes[0]);
      setIsAnalyzing(false);
    }, 3000);
  };

  const initializeMap = () => {
    const container = document.getElementById("track-map-container");
    if (!container || trackMap) return;

    const patientLocation = { lat: 28.62, lng: 77.21 };

    // Initialize TomTom map
    const map = window.tt.map({
      key: "JXPnqva3lZanMKstFTttkppZnHor4IXr",
      container: "track-map-container",
      center: [patientLocation.lng, patientLocation.lat],
      zoom: 12,
      style:
        "https://api.tomtom.com/style/1/style/22.2.1-*?map=basic_main&poi=poi_main",
    });

    map.on("load", () => {
      // Add patient marker with pulsing animation
      const patientMarkerElement = document.createElement("div");
      patientMarkerElement.innerHTML = `
        <div style="
          width: 40px;
          height: 40px;
          background-color: #ef4444;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 24px;
          color: white;
          border: 3px solid white;
          box-shadow: 0 2px 8px rgba(0,0,0,0.3);
          animation: pulse 2s infinite;
        ">🚨</div>
        <style>
          @keyframes pulse {
            0%, 100% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.1); opacity: 0.8; }
          }
        </style>
      `;

      new window.tt.Marker({ element: patientMarkerElement })
        .setLngLat([patientLocation.lng, patientLocation.lat])
        .addTo(map);

      // Draw all routes
      ambulanceRoutes.forEach((route) => {
        // Add route line
        map.addLayer({
          id: `route-${route.ambulanceId}`,
          type: "line",
          source: {
            type: "geojson",
            data: {
              type: "Feature",
              geometry: {
                type: "LineString",
                coordinates: route.path,
              },
            },
          },
          paint: {
            "line-color": route.color,
            "line-width": 5,
            "line-opacity": 0.85,
          },
        });

        // Add a thicker outline for better visibility
        map.addLayer(
          {
            id: `route-outline-${route.ambulanceId}`,
            type: "line",
            source: {
              type: "geojson",
              data: {
                type: "Feature",
                geometry: {
                  type: "LineString",
                  coordinates: route.path,
                },
              },
            },
            paint: {
              "line-color": "#ffffff",
              "line-width": 7,
              "line-opacity": 0.4,
              "line-gap-width": 0,
            },
          },
          `route-${route.ambulanceId}`
        ); // Place outline behind the main route

        // Add ambulance marker
        const ambulanceMarkerElement = document.createElement("div");
        ambulanceMarkerElement.innerHTML = `
          <div style="
            width: 42px;
            height: 42px;
            background-color: ${route.color};
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            color: white;
            border: 3px solid white;
            box-shadow: 0 3px 8px rgba(0,0,0,0.4);
            cursor: pointer;
          ">🚑</div>
        `;

        const marker = new window.tt.Marker({ element: ambulanceMarkerElement })
          .setLngLat([route.location.lng, route.location.lat])
          .addTo(map);

        const popup = new window.tt.Popup({ offset: 25 }).setHTML(`
          <div style="padding: 8px;">
            <strong>${route.ambulanceId}</strong><br/>
            ETA: ${route.eta} min<br/>
            Distance: ${route.distance} km<br/>
            Crew: ${route.crew} members
          </div>
        `);

        marker.setPopup(popup);
      });

      setTrackMap(map);
    });
  };

  useEffect(() => {
    if (trackMap && selectedAmbulance && !isAnalyzing) {
      // Highlight selected route
      ambulanceRoutes.forEach((route) => {
        if (trackMap.getLayer(`route-${route.ambulanceId}`)) {
          trackMap.setPaintProperty(
            `route-${route.ambulanceId}`,
            "line-width",
            route.ambulanceId === selectedAmbulance.ambulanceId ? 6 : 3
          );
          trackMap.setPaintProperty(
            `route-${route.ambulanceId}`,
            "line-opacity",
            route.ambulanceId === selectedAmbulance.ambulanceId ? 1 : 0.4
          );
        }
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedAmbulance, isAnalyzing, trackMap]);

  const handleAutoDispatch = async () => {
    setIsDispatching(true);

    try {
      // Fetch ambulance details to get driver phone number
      const ambulances = await ambulanceAPI.getAllAmbulances();
      const ambulance = ambulances.find(
        (amb) => amb.id === selectedAmbulance.ambulanceId
      );

      if (!ambulance) {
        alert(`Ambulance ${selectedAmbulance.ambulanceId} not found in system`);
        setIsDispatching(false);
        return;
      }

      // Prepare dispatch data with WhatsApp notification
      const dispatchData = {
        ambulance_id: selectedAmbulance.ambulanceId,
        hospital_name: "AIIMS New Delhi",
        hospital_address: "Ansari Nagar, New Delhi, Delhi 110029",
        driver_phone: ambulance.driver.phone,
        patient_info: `${emergencyData.patientName || "Unknown Patient"} - ${
          emergencyData.description
        }`,
        eta: selectedAmbulance.eta,
      };

      // Send dispatch with WhatsApp notification
      const dispatchResponse = await dispatchAPI.createDispatch(dispatchData);

      // Create emergency with assigned ambulance
      const newEmergency = {
        id: `EMG-${Date.now()}`,
        type: emergencyData.type,
        description: emergencyData.description,
        priority: emergencyData.priority,
        status: "dispatched",
        location: {
          address: emergencyData.location || "Location not specified",
          latitude: 28.62,
          longitude: 77.21,
        },
        timeReported: new Date().toISOString(),
        patientName: emergencyData.patientName || "Unknown",
        patientAge: emergencyData.patientAge || null,
        patientPhone: emergencyData.patientPhone || null,
        victims: parseInt(emergencyData.victims) || 1,
        specialRequirements: emergencyData.specialRequirements || [],
        additionalNotes: emergencyData.additionalNotes || "",
        assignedAmbulanceId: selectedAmbulance.ambulanceId,
        timeEstimatedArrival: `${selectedAmbulance.eta} min`,
        dispatchId: dispatchResponse.dispatch_id,
      };

      // Prepare success message with WhatsApp status
      const whatsappStatus = dispatchResponse.whatsapp_status;
      let message = `${selectedAmbulance.ambulanceId} dispatched successfully! ETA: ${selectedAmbulance.eta} minutes\n\n`;

      if (whatsappStatus.sent) {
        message += `✅ WhatsApp sent to ${ambulance.driver.name} (${ambulance.driver.phone})`;
      } else {
        message += `⚠️ WhatsApp failed: ${
          whatsappStatus.error || "Unknown error"
        }`;
      }

      // Navigate back to Active Emergencies with success message
      setTimeout(() => {
        navigate("/active-emergencies", {
          state: {
            newEmergency,
            message: message,
          },
        });
      }, 2000);
    } catch (error) {
      console.error("Error dispatching ambulance:", error);
      alert(
        `Failed to dispatch ambulance: ${
          error.response?.data?.detail || error.message
        }`
      );
      setIsDispatching(false);
    }
  };

  const handleManualDispatch = () => {
    if (!selectedAmbulance) return;
    setCountdown(0);
  };

  const handleSelectAmbulance = (route) => {
    setSelectedAmbulance(route);
    setCountdown(5); // Reset countdown when manually selecting
  };

  if (!emergencyData) {
    return null;
  }

  return (
    <Box sx={{ display: "flex", minHeight: "100vh", bgcolor: "#f3f4f6" }}>
      <Sidebar mobileOpen={mobileOpen} setMobileOpen={setMobileOpen} />
      <TopNavBar onMenuClick={() => setMobileOpen(true)} />

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: { xs: 2, md: 3 },
          mt: { xs: 8, md: 0 },
          ml: { md: "260px" },
        }}
      >
        {/* Page Header */}
        <Box
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            mb: 3,
          }}
        >
          <Box>
            <Typography variant="h4" fontWeight="bold" color="text.primary">
              Ambulance Route Tracking
            </Typography>
            <Typography variant="body2" color="text.secondary">
              AI-powered optimal ambulance selection in progress
            </Typography>
          </Box>
          <IconButton onClick={() => navigate("/active-emergencies")}>
            <Close />
          </IconButton>
        </Box>

        {/* Status Alert */}
        {isAnalyzing ? (
          <Alert severity="info" sx={{ mb: 3 }}>
            <Box display="flex" alignItems="center" gap={2}>
              <LinearProgress sx={{ flexGrow: 1 }} />
              <Typography variant="body2">
                AI analyzing all available routes...
              </Typography>
            </Box>
          </Alert>
        ) : isDispatching ? (
          <Alert severity="success" icon={<CheckCircle />} sx={{ mb: 3 }}>
            <Typography variant="body2" fontWeight={600}>
              Dispatching {selectedAmbulance.ambulanceId}... Please wait.
            </Typography>
          </Alert>
        ) : (
          <Alert
            severity="success"
            sx={{ mb: 3 }}
            action={
              <Chip
                label={`Auto-dispatch in ${countdown}s`}
                color="success"
                size="small"
                sx={{ fontWeight: 600 }}
              />
            }
          >
            <Typography variant="body2" fontWeight={600}>
              AI Recommendation: {selectedAmbulance.ambulanceId} is the optimal
              choice with {selectedAmbulance.eta} min ETA
            </Typography>
          </Alert>
        )}

        {/* Map */}
        <Paper
          elevation={2}
          sx={{ mb: 3, overflow: "hidden", borderRadius: 2 }}
        >
          <Box
            id="track-map-container"
            sx={{ width: "100%", height: 500, bgcolor: "#e5e7eb" }}
          />
        </Paper>

        {/* Ambulance Cards */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="h6" fontWeight={600} gutterBottom>
            Available Ambulances (Sorted by ETA)
          </Typography>
          <Box
            sx={{
              display: "grid",
              gridTemplateColumns: {
                xs: "1fr",
                sm: "1fr 1fr",
                lg: "1fr 1fr 1fr 1fr 1fr",
              },
              gap: 2,
            }}
          >
            {ambulanceRoutes.map((route, index) => (
              <Card
                key={route.ambulanceId}
                sx={{
                  cursor: "pointer",
                  border:
                    selectedAmbulance?.ambulanceId === route.ambulanceId
                      ? `3px solid ${route.color}`
                      : "1px solid #e5e7eb",
                  bgcolor:
                    selectedAmbulance?.ambulanceId === route.ambulanceId
                      ? "#f0fdf4"
                      : "white",
                  transition: "all 0.3s ease",
                  transform:
                    selectedAmbulance?.ambulanceId === route.ambulanceId
                      ? "scale(1.05)"
                      : "scale(1)",
                  boxShadow:
                    selectedAmbulance?.ambulanceId === route.ambulanceId
                      ? `0 4px 12px ${route.color}40`
                      : "none",
                }}
                onClick={() => handleSelectAmbulance(route)}
              >
                <CardContent>
                  <Box display="flex" alignItems="center" mb={1}>
                    <Box
                      sx={{
                        width: 16,
                        height: 16,
                        borderRadius: "50%",
                        bgcolor: route.color,
                        mr: 1,
                      }}
                    />
                    <Typography variant="subtitle1" fontWeight={600}>
                      {route.ambulanceId}
                    </Typography>
                  </Box>
                  {index === 0 && (
                    <Chip
                      label="AI Best Choice"
                      size="small"
                      color="success"
                      sx={{ mb: 1, fontWeight: 600 }}
                    />
                  )}
                  <Typography variant="body2" color="text.secondary">
                    ETA: <strong>{route.eta} min</strong>
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Distance: {route.distance} km
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Crew: {route.crew} members
                  </Typography>
                </CardContent>
              </Card>
            ))}
          </Box>
        </Box>

        {/* Action Buttons */}
        {!isAnalyzing && !isDispatching && (
          <Box sx={{ display: "flex", gap: 2, justifyContent: "center" }}>
            <Button
              variant="outlined"
              onClick={() => navigate("/active-emergencies")}
            >
              Cancel
            </Button>
            <Button
              variant="contained"
              color="success"
              size="large"
              startIcon={<LocalShipping />}
              onClick={handleManualDispatch}
              disabled={!selectedAmbulance}
            >
              Dispatch {selectedAmbulance?.ambulanceId} Now
            </Button>
          </Box>
        )}
      </Box>
    </Box>
  );
};

export default Track;
