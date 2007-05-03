%define	name	zlib
%define	version	1.2.3
%define release	%mkrel 5
%define	lib_major 1
%define	lib_name %{name}%{lib_major}

%define build_biarch 0
%define	biarch_bit 32
# Enable bi-arch build on ppc64, sparc64 and x86-64
%ifarch sparc64 x86_64 ppc64
%define build_biarch 1
#(peroyvind): On sparc64 compiler defaults to 32 bit, we need to ensure that it uses 64 bit at link time too
%define	biarch_bit 64
%endif

%define build_diet 1

Name:		%{name}
Summary:	The zlib compression and decompression library
Version:	%{version}
Release:	%{release}
Source0:	http://prdownloads.sourceforge.net/libpng/%{name}-%{version}.tar.bz2
Patch0:		zlib-1.2.1-glibc.patch
Patch1:		zlib-1.2.1-multibuild.patch
Patch2:		zlib-1.2.2.2-build-fPIC.patch
#Patch3:	zlib-1.1.4-gzprintf.patch.bz2
Patch4:		zlib-1.2.1.1-deb-alt-inflate.patch
#Patch5:                zlib-1.2.2.2-CAN-2005-2096.patch
BuildRequires:	setarch
Group:		System/Libraries
URL:		http://www.gzip.org/zlib/
License:	BSD
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-buildroot
%if %{build_diet}
BuildRequires:	dietlibc-devel
%endif

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
Provides:	libz = %{version}-%{release} libz1 = %{version}-%{release} %{name} = %{version}-%{release}

%description -n	%{lib_name}
The zlib compression library provides in-memory compression and
decompression functions, including integrity checks of the uncompressed
data.  This version of the library supports only one compression method
(deflation), but other algorithms may be added later, which will have
the same stream interface.  The zlib library is used by many different
system programs.

%package -n	%{lib_name}-devel
Summary:	Header files and libraries for developing apps which will use zlib
Group:		Development/C
Requires:	%{lib_name} = %{version}-%{release}
Obsoletes:	libz1-devel libz-devel zlib-devel
Provides:	libz-devel = %{version}-%{release} libz1-devel = %{version}-%{release} %{name}-devel = %{version}-%{release}

%description -n	%{lib_name}-devel
The zlib-devel package contains the header files and libraries needed
to develop programs that use the zlib compression and decompression
library.

Install the zlib-devel package if you want to develop applications that
will use the zlib library.

%prep
%setup -q
%patch0 -p1
%patch1 -p1 -b .multibuild
%patch2 -p1 -b .build-fPIC
#%patch3 -p1 -b .gzprintf
%patch4 -p1 -b .deb-alt-inflate
#%patch5 -p1 -b .can-2005-2096

%build
mkdir objs
pushd objs
  CFLAGS="$RPM_OPT_FLAGS" CC="%{__cc} -m%{biarch_bit}" \
  ../configure --shared --prefix=%{_prefix} --libdir=%{_libdir}
  %make
  make test
  ln -s ../zlib.3 .
popd

%if %{build_biarch}
RPM_OPT_FLAGS_32=`linux32 rpm --eval %%optflags`
mkdir objs32
pushd objs32
  CFLAGS="$RPM_OPT_FLAGS_32" CC="%{__cc} -m32" \
  ../configure --shared --prefix=%{_prefix}
  %make
  make test
  ln -s ../zlib.3 .
popd
%endif

%if %{build_diet}
mkdir objsdiet
pushd objsdiet
  CFLAGS="$RPM_OPT_FLAGS" CC="diet gcc" \
  ../configure --prefix=%{_prefix}
  %make libz.a
popd
%endif

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT/%{_prefix}
install -d $RPM_BUILD_ROOT/%{_libdir}

make install -C objs prefix=$RPM_BUILD_ROOT%{_prefix} libdir=$RPM_BUILD_ROOT%{_libdir}
%if %{build_biarch}
make install-libs -C objs32 prefix=$RPM_BUILD_ROOT%{_prefix}
%endif

install -d $RPM_BUILD_ROOT/%{_lib}
mv $RPM_BUILD_ROOT%{_libdir}/*.so.* $RPM_BUILD_ROOT/%{_lib}/
ln -s ../../%{_lib}/libz.so.%{version} $RPM_BUILD_ROOT%{_libdir}/

%if %{build_biarch}
install -d $RPM_BUILD_ROOT/lib
mv $RPM_BUILD_ROOT%{_prefix}/lib/*.so.* $RPM_BUILD_ROOT/lib/
ln -s ../../lib/libz.so.%{version} $RPM_BUILD_ROOT%{_prefix}/lib/
%endif

%if %{build_diet}
install objsdiet/libz.a $RPM_BUILD_ROOT%{_libdir}/libz-diet.a
%endif

%clean
rm -fr $RPM_BUILD_ROOT

%post -n %{lib_name} -p /sbin/ldconfig
%postun -n %{lib_name} -p /sbin/ldconfig

%files -n %{lib_name}
%defattr(-, root, root)
%doc README
/%{_lib}/libz.so.*
%{_libdir}/libz.so.*
%if %{build_biarch}
/lib/libz.so.*
%{_prefix}/lib/libz.so.*
%endif

%files -n %{lib_name}-devel
%defattr(-, root, root)
%doc README ChangeLog algorithm.txt
%{_libdir}/*.a
%{_libdir}/*.so
%if %{build_biarch}
%{_prefix}/lib/*.a
%{_prefix}/lib/*.so
%endif
%{_includedir}/*
%{_mandir}/*/*


