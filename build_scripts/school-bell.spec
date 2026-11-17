# RPM spec for School Bell.
# Primary target: ALT Linux. Fedora-compatible dependency names are selected
# automatically by the conditional below.

%{!?app_version:%global app_version 1.0.5}
%global debug_package %{nil}

Name:           school-bell
Version:        %{app_version}
Release:        1%{?dist}
Summary:        School bell automation with schedule, break music and announcements
Summary(ru):    Автоматизация школьных звонков: расписание и музыка на переменах
License:        MIT
URL:            https://github.com/otetswoo/python_schoolbell
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch

Requires:       python3
%if 0%{?altlinux}
Requires:       python3-module-pyside6
Requires:       python3-module-yaml
%else
Requires:       python3-pyside6
Requires:       python3-pyyaml
%endif

%description
School Bell automates lesson bells, plays break music, an anthem and
announcements according to a flexible schedule. It includes a holiday mode
and Russian/English localization.

%description -l ru
School Bell автоматизирует школьные звонки, воспроизводит музыку на
переменах, гимн и объявления по гибкому расписанию. Поддерживает режим
каникул и русскую/английскую локализацию.

%prep
%setup -q -n %{name}-%{version}

%build
# Pure Python application; nothing to compile.

%install
rm -rf %{buildroot}
install -d %{buildroot}%{_datadir}/%{name}
cp -a school_bell.py src sounds schedule.yml README.md %{buildroot}%{_datadir}/%{name}/

install -d %{buildroot}%{_bindir}
cat > %{buildroot}%{_bindir}/%{name} <<'EOF'
#!/bin/sh
exec python3 /usr/share/school-bell/school_bell.py "$@"
EOF
chmod 755 %{buildroot}%{_bindir}/%{name}

install -Dpm 644 school-bell.desktop %{buildroot}%{_datadir}/applications/%{name}.desktop
install -Dpm 644 school-bell.png %{buildroot}%{_datadir}/icons/hicolor/256x256/apps/%{name}.png

%post
if [ -x /usr/bin/update-desktop-database ]; then
    update-desktop-database /usr/share/applications >/dev/null 2>&1 || true
fi
if [ -x /usr/bin/gtk-update-icon-cache ]; then
    gtk-update-icon-cache -f /usr/share/icons/hicolor >/dev/null 2>&1 || true
fi

%postun
if [ -x /usr/bin/update-desktop-database ]; then
    update-desktop-database /usr/share/applications >/dev/null 2>&1 || true
fi
if [ -x /usr/bin/gtk-update-icon-cache ]; then
    gtk-update-icon-cache -f /usr/share/icons/hicolor >/dev/null 2>&1 || true
fi

%files
%{_bindir}/%{name}
%{_datadir}/%{name}
%{_datadir}/applications/%{name}.desktop
%{_datadir}/icons/hicolor/256x256/apps/%{name}.png

%changelog
* Tue Nov 17 2026 otetswoo <otetswoo@users.noreply.github.com> - %{version}-1
- Initial RPM package
