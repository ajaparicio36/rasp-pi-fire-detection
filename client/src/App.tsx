import { useEffect, useState } from "react";
import { io, Socket } from "socket.io-client";
import CameraFeed from "./components/CameraFeed";
// import DataChart from "./components/DataChart";
// import AlarmControl from "./components/AlarmControl";

function App() {
  const [socket, setSocket] = useState<Socket | null>(null);

  useEffect(() => {
    const newSocket = io("http://localhost:5000");
    setSocket(newSocket);

    return () => {
      newSocket.close();
    };
  }, []);

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Fire Detection System</h1>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <CameraFeed socket={socket} />
          {/* <div className="space-y-8">
            <DataChart socket={socket} />
            <AlarmControl socket={socket} />
          </div> */}
        </div>
      </div>
    </div>
  );
}

export default App;
