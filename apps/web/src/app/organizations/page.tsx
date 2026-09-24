import { OrganizationDirectoryScreen } from "@/components/screens/phase5";
import { getRepository } from "@/data";

export default async function Page() {
  return <OrganizationDirectoryScreen rows={await getRepository().listOrganizations()} />;
}
