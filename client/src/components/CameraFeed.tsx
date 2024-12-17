// src/components/CameraFeed.tsx
import { useEffect, useRef, useState } from "react";
import { Socket } from "socket.io-client";

interface CameraFeedProps {
  socket: Socket | null;
}

const CameraFeed = ({ socket }: CameraFeedProps) => {
  const imageRef = useRef<HTMLImageElement>(null);
  const [isFireDetected, setIsFireDetected] = useState(false);
  const [fireConfidence, setFireConfidence] = useState(0);

  useEffect(() => {
    if (!socket) return;

    const handleFrame = (data: {
      frame: string;
      fire_detected: boolean;
      fire_confidence: number;
    }) => {
      if (imageRef.current) {
        imageRef.current.src = `data:image/jpeg;base64,${data.frame}`;
      }

      // Update fire detection state
      setIsFireDetected(data.fire_detected);
      setFireConfidence(data.fire_confidence);
    };

    socket.on("camera_frame", handleFrame);

    return () => {
      socket.off("camera_frame", handleFrame);
    };
  }, [socket]);

  return (
    <div className="relative bg-gray-900 rounded-lg overflow-hidden shadow-lg">
      {/* Fire Detection Warning */}
      {isFireDetected && (
        <div className="absolute top-0 left-0 right-0 bg-red-600 text-white text-center py-2 z-10">
          🔥 FIRE DETECTED! Confidence: {(fireConfidence * 100).toFixed(2)}%
        </div>
      )}

      <div className="aspect-video relative">
        <img
          ref={imageRef}
          className="absolute inset-0 w-full h-full object-contain"
          alt="Camera Feed"
        />
      </div>
      <div className="absolute top-4 left-4">
        <div className="flex items-center">
          <div className="h-3 w-3 bg-red-500 rounded-full animate-pulse"></div>
          <span className="ml-2 text-white text-sm font-medium">Live</span>
        </div>
      </div>
    </div>
  );
};

export default CameraFeed;
