import { useEffect, useState } from "react";
import { Socket } from "socket.io-client";
import { Bell, BellOff, Shield, ShieldAlert, Flame } from "lucide-react";

interface AlarmControlProps {
  socket: Socket | null;
}

interface Status {
  smoke_detected: boolean;
  alarm_active: boolean;
  alarm_enabled: boolean;
}

const AlarmControl = ({ socket }: AlarmControlProps) => {
  const [status, setStatus] = useState<Status>({
    smoke_detected: false,
    alarm_active: false,
    alarm_enabled: true,
  });

  useEffect(() => {
    if (!socket) return;

    socket.on("status_update", (newStatus: Status) => {
      setStatus(newStatus);
    });

    socket.emit("get_status");

    return () => {
      socket.off("status_update");
    };
  }, [socket]);

  const handleToggleAlarm = () => {
    if (socket) {
      socket.emit("toggle_alarm");
      console.log("Toggled alarm");
    }
  };

  return (
    <div className="bg-white/95 backdrop-blur-sm rounded-xl shadow-lg p-6 border border-gray-100">
      <div className="flex items-center justify-between mb-8">
        <h2 className="text-2xl font-bold bg-gradient-to-r from-red-600 to-orange-600 bg-clip-text text-transparent">
          System Control
        </h2>
        <button
          onClick={handleToggleAlarm}
          className={`px-6 py-3 rounded-lg flex items-center gap-2 transition-all duration-300 ${
            status.alarm_enabled
              ? "bg-red-600 text-white hover:bg-red-700 shadow-lg shadow-red-600/20"
              : "bg-gray-100 text-gray-600 hover:bg-gray-200"
          }`}
        >
          {status.alarm_enabled ? (
            <>
              <Bell className="animate-bounce" size={20} /> Disable Alarm
            </>
          ) : (
            <>
              <BellOff size={20} /> Enable Alarm
            </>
          )}
        </button>
      </div>

      <div className="grid grid-cols-1 gap-4">
        <StatusCard
          icon={<Flame size={20} />}
          title="Smoke Detection"
          status={status.smoke_detected}
          activeText="DETECTED"
          inactiveText="Clear"
          activeClass="bg-red-100"
          activeBadgeClass="bg-red-200 text-red-800"
          inactiveClass="bg-gray-50"
          inactiveBadgeClass="bg-gray-200 text-gray-800"
        />

        <StatusCard
          icon={<ShieldAlert size={20} />}
          title="Alarm Status"
          status={status.alarm_active}
          activeText="ACTIVE"
          inactiveText="Inactive"
          activeClass="bg-red-100"
          activeBadgeClass="bg-red-200 text-red-800"
          inactiveClass="bg-gray-50"
          inactiveBadgeClass="bg-gray-200 text-gray-800"
        />

        <StatusCard
          icon={<Shield size={20} />}
          title="System Status"
          status={status.alarm_enabled}
          activeText="ARMED"
          inactiveText="DISARMED"
          activeClass="bg-green-100"
          activeBadgeClass="bg-green-200 text-green-800"
          inactiveClass="bg-yellow-100"
          inactiveBadgeClass="bg-yellow-200 text-yellow-800"
        />
      </div>
    </div>
  );
};

interface StatusCardProps {
  icon: React.ReactNode;
  title: string;
  status: boolean;
  activeText: string;
  inactiveText: string;
  activeClass: string;
  activeBadgeClass: string;
  inactiveClass: string;
  inactiveBadgeClass: string;
}

const StatusCard = ({
  icon,
  title,
  status,
  activeText,
  inactiveText,
  activeClass,
  activeBadgeClass,
  inactiveClass,
  inactiveBadgeClass,
}: StatusCardProps) => (
  <div
    className={`p-4 rounded-lg transition-all duration-300 ${
      status ? activeClass : inactiveClass
    }`}
  >
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        {icon}
        <span className="font-medium">{title}</span>
      </div>
      <span
        className={`px-3 py-1 rounded-full text-sm font-medium transition-all duration-300 ${
          status ? activeBadgeClass : inactiveBadgeClass
        }`}
      >
        {status ? activeText : inactiveText}
      </span>
    </div>
  </div>
);

export default AlarmControl;
