export type MockItem = {
  id: string;
  title: string;
  description: string;
  tag: string;
  type: "external" | "local";
  href: string;
};

export const doctrineMockItems: MockItem[] = [
  {
    id: "doc-1",
    title: "DHA Policies Reference Center",
    description: "Primary source directory for DHA policy memoranda and updates.",
    tag: "Policy",
    type: "external",
    href: "https://www.health.mil/Reference-Center/Policies",
  },
  {
    id: "doc-2",
    title: "DoD Instructions Directory",
    description: "Official DoDI listings for governance and compliance references.",
    tag: "Governance",
    type: "external",
    href: "https://www.esd.whs.mil/Directives/issuances/dodi/",
  },
  {
    id: "doc-3",
    title: "AFSC Officer Quick Reference",
    description: "Officer AFSC mapping and quick lookup guide.",
    tag: "Career",
    type: "local",
    href: "example-doctrine-1.pdf",
  },
  {
    id: "doc-4",
    title: "AFSC Enlisted Quick Reference",
    description: "Enlisted AFSC quick reference for manpower and classification support.",
    tag: "Career",
    type: "local",
    href: "example-doctrine-2.pdf",
  },
  {
    id: "doc-5",
    title: "MSC Career Progression Guide",
    description: "Narrative guide for MSC progression, roles, and development milestones.",
    tag: "Development",
    type: "local",
    href: "example-doctrine-3.pdf",
  },
];

export const toolkitMockItems: MockItem[] = [
  {
    id: "tool-1",
    title: "AFMS MSC Landing Page",
    description: "Top-level Medical Service Corps information from AFMS.",
    tag: "Official",
    type: "external",
    href: "https://www.airforcemedicine.af.mil/About-Us/Medical-Branches/Medical-Service-Corps/",
  },
  {
    id: "tool-2",
    title: "DHA Strategy Overview",
    description: "DHA strategic priorities and organizational direction.",
    tag: "Strategy",
    type: "external",
    href: "https://www.dha.mil/About-DHA/DHA-Strategy",
  },
  {
    id: "tool-3",
    title: "AFMEDCOM Quick Reference",
    description: "Rapid orientation guide for AFMEDCOM structure and touchpoints.",
    tag: "Reference",
    type: "local",
    href: "example-toolkit-1.pdf",
  },
  {
    id: "tool-4",
    title: "DHA Network Structure",
    description: "Overview of DHA network relationships and organizational components.",
    tag: "Organization",
    type: "local",
    href: "example-toolkit-2.pdf",
  },
  {
    id: "tool-5",
    title: "MSC Mentor Guide",
    description: "Mentorship framework and practical guidance for MSC officers.",
    tag: "Mentorship",
    type: "local",
    href: "example.pdf",
  },
];
