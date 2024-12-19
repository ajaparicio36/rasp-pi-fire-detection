import { useEffect, useState } from "react";
import { Socket } from "socket.io-client";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import { Line } from "react-chartjs-2";
import { Activity, Bell, Clock, ToggleLeft } from "lucide-react";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

interface DataPoint {
  timestamp: string;
  smoke_detected: boolean;
  alarm_active: boolean;
  alarm_enabled: boolean;
}

interface Summary {
  smoke_detections: number;
  alarm_activations: number;
  uptime: number;
  error?: string;
}

interface DataChartProps {
  socket: Socket | null;
}

const DataChart = ({ socket }: DataChartProps) => {
  const [dataPoints, setDataPoints] = useState<DataPoint[]>([]);
  const [summary, setSummary] = useState<Summary>({
    smoke_detections: 0,
    alarm_activations: 0,
    uptime: 0,
  });

  const filterDataPoints = (
    data: DataPoint[],
    intervalSeconds: number,
    totalSeconds: number
  ) => {
    const now = new Date().getTime();
    const oldestAllowedTime = now - totalSeconds * 1000;
    return data
      .filter(
        (point) => new Date(point.timestamp).getTime() > oldestAllowedTime
      )
      .filter(
        (_, index, array) =>
          index %
            Math.round(
              intervalSeconds /
                ((now - new Date(array[0].timestamp).getTime()) /
                  1000 /
                  array.length)
            ) ===
          0
      )
      .slice(-Math.floor(totalSeconds / intervalSeconds));
  };

  useEffect(() => {
    if (!socket) return;

    socket.on(
      "full_dataset",
      (data: { data: DataPoint[]; summary: Summary }) => {
        setDataPoints(filterDataPoints(data.data, 10, 120));
        setSummary(data.summary);
      }
    );

    socket.on("new_data_point", (point: DataPoint) => {
      setDataPoints((prev) => filterDataPoints([...prev, point], 10, 120));
    });

    // Request initial data
    socket.emit("get_historical_data");

    return () => {
      socket.off("full_dataset");
      socket.off("new_data_point");
    };
  }, [socket]);

  const chartData = {
    labels: dataPoints.map((point) => {
      const date = new Date(point.timestamp);
      return date.toLocaleTimeString([], {
        minute: "2-digit",
        second: "2-digit",
      });
    }),
    datasets: [
      {
        label: "Smoke Detected",
        data: dataPoints.map((point) => (point.smoke_detected ? 1 : 0)),
        borderColor: "rgb(239, 68, 68)",
        backgroundColor: "rgba(239, 68, 68, 0.5)",
        tension: 0.2,
      },
      {
        label: "Alarm Active",
        data: dataPoints.map((point) => (point.alarm_active ? 1 : 0)),
        borderColor: "rgb(59, 130, 246)",
        backgroundColor: "rgba(59, 130, 246, 0.5)",
        tension: 0.2,
      },
      {
        label: "Alarm Enabled",
        data: dataPoints.map((point) => (point.alarm_enabled ? 1 : 0)),
        borderColor: "rgb(34, 197, 94)",
        backgroundColor: "rgba(34, 197, 94, 0.5)",
        tension: 0.2,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: "top" as const,
      },
      title: {
        display: true,
        text: "System Activity Monitor",
        font: {
          size: 16,
          weight: "bold" as const,
        },
        padding: 20,
      },
    },
    scales: {
      x: {
        ticks: {
          maxTicksLimit: 12,
          maxRotation: 0,
          minRotation: 0,
        },
      },
      y: {
        min: 0,
        max: 1,
        ticks: {
          stepSize: 1,
        },
      },
    },
  };

  return (
    <div className="bg-white/95 backdrop-blur-sm rounded-xl shadow-lg p-6 border border-gray-100">
      <div className="grid grid-cols-4 gap-4 mb-8">
        <StatCard
          icon={<Activity className="text-blue-600" />}
          title="Smoke Detections"
          value={summary.smoke_detections}
          bgColor="bg-blue-50"
          textColor="text-blue-900"
          valueColor="text-blue-600"
        />
        <StatCard
          icon={<Bell className="text-red-600" />}
          title="Alarm Activations"
          value={summary.alarm_activations}
          bgColor="bg-red-50"
          textColor="text-red-900"
          valueColor="text-red-600"
        />
        <StatCard
          icon={<Clock className="text-green-600" />}
          title="Uptime"
          value={`${Math.floor(summary.uptime / 60)}m ${Math.floor(
            summary.uptime % 60
          )}s`}
          bgColor="bg-green-50"
          textColor="text-green-900"
          valueColor="text-green-600"
        />
        <StatCard
          icon={<ToggleLeft className="text-purple-600" />}
          title="System Status"
          value={summary.error ? "Error" : "Operational"}
          bgColor="bg-purple-50"
          textColor="text-purple-900"
          valueColor={summary.error ? "text-red-600" : "text-purple-600"}
        />
      </div>
      <div className="h-[300px]">
        <Line options={options} data={chartData} />
      </div>
      {summary.error && (
        <div className="mt-4 p-4 bg-red-50 rounded-lg border border-red-200">
          <p className="text-red-700 text-sm">Error: {summary.error}</p>
        </div>
      )}
    </div>
  );
};

interface StatCardProps {
  icon: React.ReactNode;
  title: string;
  value: string | number;
  bgColor: string;
  textColor: string;
  valueColor: string;
}

const StatCard = ({
  icon,
  title,
  value,
  bgColor,
  textColor,
  valueColor,
}: StatCardProps) => (
  <div
    className={`${bgColor} p-4 rounded-lg transition-all duration-300 hover:shadow-md`}
  >
    <div className="flex items-center gap-2 mb-2">
      {icon}
      <h3 className={`text-sm font-medium ${textColor}`}>{title}</h3>
    </div>
    <p className={`text-2xl font-bold ${valueColor}`}>{value}</p>
  </div>
);

export default DataChart;
