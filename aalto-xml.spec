Name:		aalto-xml
Version:	1.4.0
Release:	1
Summary:	Non-blocking StAX and SAX XML processor
Group:		Development/Java
License:	ASL 2.0
URL:		https://github.com/FasterXML/aalto-xml
Source0:	https://github.com/FasterXML/aalto-xml/archive/refs/tags/aalto-xml-%{version}.tar.gz#/aalto-xml-%{version}.tar.gz

BuildArch:	noarch
Obsoletes:	%{name}-javadoc < %{version}
BuildRequires:	mvn(com.fasterxml:oss-parent:pom::)
# oss-parent pins the compiler plugin to this ASM jar.
BuildRequires:	mvn(org.ow2.asm:asm)
BuildRequires:	mvn(org.codehaus.woodstox:stax2-api)
# Literal, so the first rpmbuild -bs records them before sysjar is installed.
BuildRequires:	maven
BuildRequires:	java-current-devel
BuildSystem:	maven
BuildOption(install):	--file-name aalto-xml

%description
Aalto is a StAX and SAX XML processor aimed at fast parsing and
non-blocking input. 1.4.0 requires Java 8. It completes XMLStreamWriter
validation and fixes namespace repair, CDATA boundaries, and DTD root
names. It implements StAX2. Tests are skipped. The OSGi bundle
descriptor and the Java module descriptor are left out.

%prep
%autosetup -n aalto-xml-aalto-xml-%{version}
# packaging bundle needs the Felix plugin, which is not packaged.
# Moditect is on the keep list and would run during package.
# JaCoCo binds prepare-agent to initialize. Test dependencies are
# JUnit 5 and Woodstox. .mvn points the wrapper at a Maven download.
python - <<'PY'
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

ET.register_namespace("", "http://maven.apache.org/POM/4.0.0")
ET.register_namespace("xsi", "http://www.w3.org/2001/XMLSchema-instance")

def local(tag):
    return tag.rsplit("}", 1)[-1]

drop_plugins = {
    "central-publishing-maven-plugin",
    "moditect-maven-plugin",
    "jacoco-maven-plugin",
    "maven-surefire-plugin",
}

path = Path("pom.xml")
tree = ET.parse(path)
root = tree.getroot()
packaging = None
removed = []
removed_tests = 0
kept_stax = False
for parent in list(root.iter()):
    for child in list(parent):
        name = local(child.tag)
        if name == "packaging" and (child.text or "").strip() == "bundle":
            child.text = "jar"
            packaging = "jar"
        if name == "dependency" and local(parent.tag) == "dependencies":
            artifact = ""
            scope = ""
            for item in child:
                if local(item.tag) == "artifactId":
                    artifact = (item.text or "").strip()
                if local(item.tag) == "scope":
                    scope = (item.text or "").strip()
            if artifact == "stax2-api" and scope != "test":
                kept_stax = True
                continue
            if scope == "test":
                parent.remove(child)
                removed_tests += 1
            continue
        if name != "plugin":
            continue
        artifact = ""
        for item in child:
            if local(item.tag) == "artifactId":
                artifact = (item.text or "").strip()
        if artifact in drop_plugins:
            parent.remove(child)
            removed.append(artifact)
if packaging != "jar" or sorted(removed) != sorted(drop_plugins) or removed_tests != 2 or not kept_stax:
    raise SystemExit(
        f"packaging={packaging} removed={removed} tests={removed_tests} stax={kept_stax}"
    )
tree.write(path, encoding="UTF-8", xml_declaration=True)
wrapper = Path(".mvn")
if not wrapper.is_dir():
    raise SystemExit(".mvn missing")
shutil.rmtree(wrapper)
PY

%files -f .mfiles
%doc LICENSE README.md release-notes/VERSION
