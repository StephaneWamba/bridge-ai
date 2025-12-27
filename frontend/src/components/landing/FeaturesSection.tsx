"use client";

import { Bot, Link2, Mail, Calendar, MessageSquare, Zap } from "lucide-react";

const features = [
  {
    icon: Bot,
    title: "AI Agent",
    description: "Intelligent automation powered by advanced AI",
  },
  {
    icon: Link2,
    title: "HubSpot Integration",
    description: "Seamless CRM sync and data management",
  },
  {
    icon: Mail,
    title: "Gmail & Calendar",
    description: "Email and scheduling automation",
  },
  {
    icon: MessageSquare,
    title: "Discord",
    description: "Team chat integration and notifications",
  },
  {
    icon: Calendar,
    title: "Calendar",
    description: "Smart scheduling and event management",
  },
  {
    icon: Zap,
    title: "Fast Response",
    description: "Real-time processing and instant results",
  },
];

export function FeaturesSection() {
  return (
    <section id="features" className="py-24 bg-[#0A0A0A] border-t border-gray-800/50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            Powerful Features
          </h2>
          <p className="text-lg text-gray-400 max-w-2xl mx-auto">
            Everything you need to automate your business workflows
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature) => {
            const Icon = feature.icon;
            return (
              <div
                key={feature.title}
                className="group relative p-6 rounded-xl bg-gray-900/50 border border-gray-800/50 hover:border-gray-700/50 transition-all duration-200 hover:bg-gray-900/70"
              >
                <div className="flex items-start space-x-4">
                  <div className="flex-shrink-0 w-12 h-12 rounded-lg bg-gray-800/50 flex items-center justify-center group-hover:bg-gray-700/50 transition-colors">
                    <Icon className="w-6 h-6 text-white" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-white mb-2">
                      {feature.title}
                    </h3>
                    <p className="text-sm text-gray-400 leading-relaxed">
                      {feature.description}
                    </p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

