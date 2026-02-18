"use client";

import {
  ResponsiveContainer,
  AreaChart,
  Area,
} from "recharts";

interface SparkLineProps {
  data: number[];
  color?: string;
}

export default function SparkLine({
  data,
  color = "#6366f1",
}: SparkLineProps) {
  const chartData = data.map((value, i) => ({ v: value, i }));

  return (
    <ResponsiveContainer width="100%" height={40}>
      <AreaChart data={chartData}>
        <defs>
          <linearGradient id={`grad-${color}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity={0.3} />
            <stop offset="100%" stopColor={color} stopOpacity={0} />
          </linearGradient>
        </defs>
        <Area
          type="monotone"
          dataKey="v"
          stroke={color}
          strokeWidth={1.5}
          fill={`url(#grad-${color})`}
          dot={false}
          isAnimationActive={false}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
