import { useEffect, useRef, useState } from "react";
import { Socket } from "socket.io-client";
import { Camera, AlertTriangle } from "lucide-react";

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
      setIsFireDetected(data.fire_detected);
      setFireConfidence(data.fire_confidence);
    };

    socket.on("camera_frame", handleFrame);

    return () => {
      socket.off("camera_frame", handleFrame);
    };
  }, [socket]);

  return (
    <div className="relative bg-gray-900 rounded-xl overflow-hidden shadow-lg border border-gray-800">
      {isFireDetected && (
        <div className="absolute top-0 left-0 right-0 bg-red-600 text-white py-3 z-10 animate-pulse">
          <div className="flex items-center justify-center gap-2">
            <AlertTriangle className="animate-bounce" />
            <span className="font-bold">
              FIRE DETECTED! Confidence: {(fireConfidence * 100).toFixed(2)}%
            </span>
          </div>
        </div>
      )}

      <div className="aspect-video relative">
        <img
          ref={imageRef}
          className="absolute inset-0 w-full h-full object-contain"
          alt="Camera Feed"
        />
        <div className="absolute top-4 left-4 flex items-center gap-4">
          <div className="flex items-center gap-2 bg-black/50 backdrop-blur-sm px-3 py-1.5 rounded-full">
            <div className="h-2 w-2 bg-red-500 rounded-full animate-pulse"></div>
            <span className="text-white text-sm font-medium">Live</span>
          </div>
          <div className="flex items-center gap-2 bg-black/50 backdrop-blur-sm px-3 py-1.5 rounded-full">
            <Camera size={16} className="text-white" />
            <span className="text-white text-sm font-medium">Camera 1</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CameraFeed;
