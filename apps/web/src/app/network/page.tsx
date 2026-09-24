import { NetworkScreen } from "@/components/screens/phase5";
import { getRepository, resolveDataSource } from "@/data";

export default async function Page({
  searchParams,
}: {
  searchParams: Promise<{ focus?: string }>;
}) {
  const { focus } = await searchParams;
  if (
    resolveDataSource({ NEXT_PUBLIC_DATA_SOURCE: process.env.NEXT_PUBLIC_DATA_SOURCE }) === "mock"
  )
    return <NetworkScreen />;
  return (
    <NetworkScreen initialNetwork={await getRepository().getNetwork(focus)} initialFocus={focus} />
  );
}
