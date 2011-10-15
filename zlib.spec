%define lib_major 1
%define lib_name %{name}%{lib_major}
#fix in future release
#% define libname % mklibname % {name} % {api} % {major}
#% define develname % mklibname % {name} -d

Summary:	The zlib compression and decompression library
Name:		zlib
Version:	1.2.5
Release:	%mkrel 11
Group:		System/Libraries
Source0:	http://www.zlib.net/zlib-%{version}.tar.bz2
Patch3:		zlib-1.2.4-autotools.patch
# https://bugzilla.redhat.com/show_bug.cgi?id=591317
Patch4:		zlib-1.2.5-gentoo.patch
Patch5:		minizip-null.patch
URL:		http://www.gzip.org/zlib/
# /contrib/dotzlib/ have Boost license
License:	BSD
#BuildRoot:	% {_tmppath}/% {name}-% {version}-% {release}-root-% (% {__id_u} -n)
BuildRequires:	automake, autoconf, libtool

%description
The zlib compression library provides in-memory compression and
decompression functions, including integrity checks of the uncompressed
data.  This version of the library supports only one compression method
(deflation), but other algorithms may be added later, which will have
the same stream interface.  The zlib library is used by many different
system programs.


%package -n	%{lib_name}
Summary:	The zlib compression and decompression library
Group:		System/Libraries
Obsoletes:	libz, libz1, %{name}

%package -n	%{lib_name}-devel
Summary:	Header files and libraries for Zlib development
Group:		Development/C
Obsoletes:	libz1-devel libz-devel zlib-devel
Provides:	zlib-devel
Provides:	libz-devel

Requires:	%{lib_name} = %{version}-%{release}

%description -n %{lib_name}-devel
The zlib-devel package contains the header files and libraries needed
to develop programs that use the zlib compression and decompression
library.

Install the zlib-devel package if you want to develop applications that
will use the zlib library.

%package -n	%{lib_name}-static
Summary:	Static libraries for Zlib development
Group:		System/Libraries
Requires:	%{lib_name} = %{version}-%{release}


%description -n	%{lib_name}-static
The zlib-static package includes static libraries needed
to develop programs that use the zlib compression and
decompression library.

%package -n	%{lib_name}-minizip
Summary:	Minizip manipulates files from a .zip archive
Group:		System/Libraries
Obsoletes:	minizip-devel
Requires:	%{lib_name} = %{version}-%{release}

%description -n	%{lib_name}-minizip
Minizip manipulates files from a .zip archive.

%package -n	%{lib_name}-minizip-devel
Summary:	Development files for the minizip library
Group:		System/Libraries
Requires:	%{lib_name}-minizip = %{version}-%{release}
Requires:	%{lib_name}-devel = %{version}-%{release}
Requires:	pkgconfig

%description -n %{lib_name}-minizip-devel
This package contains the libraries and header files needed for
developing applications which use minizip.

%prep
%setup -q
%patch3 -p1 -b .atools
%patch4 -p1 -b .g
%patch5 -p1 -b .null
# patch cannot create an empty dir
mkdir contrib/minizip/m4
cp minigzip.c contrib/minizip
iconv -f windows-1252 -t utf-8 <ChangeLog >ChangeLog.tmp
mv ChangeLog.tmp ChangeLog

%build
CFLAGS=$RPM_OPT_FLAGS ./configure --libdir=%{_libdir} --includedir=%{_includedir} --prefix=%{_prefix}
make %{?_smp_mflags}

cd contrib/minizip
autoreconf --install
%configure  CPPFLAGS="-I/$RPM_BUILD_DIR/%{name}-%{version}-%{release}"
      LDFLAGS="-L/$RPM_BUILD_DIR/%{name}-%{version}-%{release}"

make %{?_smp_mflags}

%check
make test

%install
rm -rf ${RPM_BUILD_ROOT}

make install DESTDIR=$RPM_BUILD_ROOT
mkdir $RPM_BUILD_ROOT/%{_lib}
mv $RPM_BUILD_ROOT%{_libdir}/libz.so.* $RPM_BUILD_ROOT/%{_lib}/

reldir=$(echo %{_libdir} | sed 's,/$,,;s,/[^/]\+,../,g')%{_lib}
oldlink=$(readlink $RPM_BUILD_ROOT%{_libdir}/libz.so)
ln -sf $reldir/$(basename $oldlink) $RPM_BUILD_ROOT%{_libdir}/libz.so

cd contrib/minizip
make install DESTDIR=$RPM_BUILD_ROOT

rm -f $RPM_BUILD_ROOT%{_libdir}/*.la

%clean
rm -rf ${RPM_BUILD_ROOT}

%post -n %{lib_name} -p /sbin/ldconfig

%postun -n %{lib_name} -p /sbin/ldconfig

%post -n %{lib_name}-minizip -p /sbin/ldconfig

%postun -n %{lib_name}-minizip -p /sbin/ldconfig

%files -n %{lib_name}
%defattr(-,root,root,-)
%doc README ChangeLog FAQ
/%{_lib}/libz.so.*

%files -n %{lib_name}-devel
%defattr(-,root,root,-)
%doc README doc/algorithm.txt example.c
%{_libdir}/libz.so
%{_includedir}/zconf.h
%{_includedir}/zlib.h
%{_mandir}/man3/zlib.3*
%{_libdir}/pkgconfig/zlib.pc

%files -n %{lib_name}-static
%defattr(-,root,root,-)
%doc README
%{_libdir}/libz.a

%files -n %{lib_name}-minizip
%defattr(-,root,root,-)
%doc contrib/minizip/MiniZip64_info.txt contrib/minizip/MiniZip64_Changes.txt
%{_libdir}/libminizip.so.*

%files -n %{lib_name}-minizip-devel
%defattr(-,root,root,-)
%dir %{_includedir}/minizip
%{_includedir}/minizip/*.h
%{_libdir}/libminizip.so
%{_libdir}/pkgconfig/minizip.pc
