import { useEffect, useState } from "react";
import { io, Socket } from "socket.io-client";
import CameraFeed from "./components/CameraFeed";
import DataChart from "./components/DataChart";
import AlarmControl from "./components/AlarmControl";
import { Flame, AlertTriangle, Menu } from "lucide-react";
import "./App.css";

function App() {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  useEffect(() => {
    const newSocket = io("http://192.168.68.180:5000/");
    setSocket(newSocket);

    return () => {
      newSocket.close();
    };
  }, []);

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100">
      {/* Sidebar */}
      <div
        className={`fixed top-0 left-0 h-full w-16 bg-gray-800 border-r border-gray-700 z-50 transition-all duration-300 ${
          isSidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <button
          onClick={() => setIsSidebarOpen(!isSidebarOpen)}
          className="w-full p-4 hover:bg-gray-700 transition-colors"
        >
          <Menu size={24} />
        </button>
        <div className="p-4">
          <Flame className="w-8 h-8 text-red-500 mb-8" />
        </div>
      </div>

      {/* Main Content */}
      <div
        className={`transition-all duration-300 ${
          isSidebarOpen ? "pl-16" : "pl-0"
        }`}
      >
        {/* Header */}
        <header className="bg-gradient-to-r from-gray-800 to-gray-900 border-b border-gray-700 p-6">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="bg-red-500/10 p-2 rounded-lg">
                <Flame className="h-8 w-8 text-red-500" />
              </div>
              <div>
                <h1 className="text-2xl font-bold">Fire Detection System</h1>
                <p className="text-gray-400 text-sm">
                  Real-time monitoring and alert system
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center bg-red-500/10 px-4 py-2 rounded-lg">
                <div className="h-2 w-2 bg-red-500 rounded-full animate-pulse mr-2" />
                <span className="text-sm font-medium text-red-500">
                  System Active
                </span>
              </div>
              <AlertTriangle className="h-6 w-6 text-yellow-500 animate-pulse" />
            </div>
          </div>
        </header>

        {/* Main Content Area */}
        <main className="p-6">
          <div className="max-w-7xl mx-auto">
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
              <div className="space-y-6">
                <div className="bg-gray-800 rounded-xl border border-gray-700 shadow-lg overflow-hidden">
                  <div className="p-4 border-b border-gray-700 flex items-center justify-between">
                    <h2 className="font-semibold">Camera Feed</h2>
                    <span className="text-xs text-gray-400">Camera 1</span>
                  </div>
                  <CameraFeed socket={socket} />
                </div>
                <div className="bg-gray-800 rounded-xl border border-gray-700 shadow-lg">
                  <div className="p-4 border-b border-gray-700">
                    <h2 className="font-semibold">System Controls</h2>
                  </div>
                  <AlarmControl socket={socket} />
                </div>
              </div>
              <div className="bg-gray-800 rounded-xl border border-gray-700 shadow-lg">
                <div className="p-4 border-b border-gray-700">
                  <h2 className="font-semibold">Analytics</h2>
                </div>
                <DataChart socket={socket} />
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
