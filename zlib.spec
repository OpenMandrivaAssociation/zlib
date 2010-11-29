%define	lib_major 1
%define	lib_name %mklibname %{name}%{lib_major}
%define	devel_name %mklibname %{name} -d

%define build_biarch 0
# Enable bi-arch build on ppc64, sparc64 and x86-64
%ifarch sparcv9 sparc64 x86_64 ppc64
%define build_biarch 1
%endif
%ifarch sparcv9
%define	_lib	lib64
%endif

%bcond_without uclibc
%bcond_without dietlibc

Summary:	The zlib compression and decompression library
Name:		zlib
Version:	1.2.5
Release:	%mkrel 1
Group:		System/Libraries
License:	BSD
URL:		http://www.gzip.org/zlib/
Source0:	http://prdownloads.sourceforge.net/libpng/%{name}-%{version}.tar.gz
Patch1:		zlib-1.2.5-multibuild.patch
BuildRequires:	setarch
%if %{with uclibc}
BuildRequires:	uClibc-devel
%endif
%if %{with dietlibc}
BuildRequires:	dietlibc-devel
%endif
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-buildroot

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
%if %{with uclibc}
Provides:	uClibc-zlib = %{version}-%{release} uClibc-zlib1 = %{version}-%{release}
Obsoletes:	uClibc-zlib <= %{version}-%{release} uClibc-zlib1 <= %{version}-%{release}
%endif 

%description -n	%{lib_name}
The zlib compression library provides in-memory compression and
decompression functions, including integrity checks of the uncompressed
data.  This version of the library supports only one compression method
(deflation), but other algorithms may be added later, which will have
the same stream interface.  The zlib library is used by many different
system programs.

%package -n	%{devel_name}
Summary:	Header files and libraries for developing apps which will use zlib
Group:		Development/C
Requires:	%{lib_name} = %{version}-%{release}
Obsoletes:	libz1-devel libz-devel zlib-devel zlib1-devel
Provides:	libz-devel = %{version}-%{release} lib%{name}-devel = %{version}-%{release} %{name}-devel = %{version}-%{release}
%if %{with uclibc}
Provides:	uClibc-zlib-devel = %{version}-%{release} uClibc-zlib1-devel = %{version}-%{release}
Obsoletes:	uClibc-zlib-devel <= %{version}-%{release} uClibc-zlib1-devel <= %{version}-%{release}
%endif 

%description -n	%{devel_name}
The zlib-devel package contains the header files and libraries needed
to develop programs that use the zlib compression and decompression
library.

Install the zlib-devel package if you want to develop applications that
will use the zlib library.

%prep
%setup -q
%patch1 -p1 -b .multibuild~

%build
#(peroyvind): be sure to remove -m64/-m32 flags as they're not overridable
RPM_OPT_FLAGS="`echo $RPM_OPT_FLAGS| sed -e 's/-m.. //g'`"
mkdir objs
pushd objs
  CFLAGS="$RPM_OPT_FLAGS" \
%if %{build_biarch}
  CC="%{__cc} -m64" \
%endif
  ../configure --shared --prefix=%{_prefix} --libdir=%{_libdir}
  %make
  make test
  ln -s ../zlib.3 .
popd

%if %{build_biarch}
%ifarch %{sunsparc}
RPM_OPT_FLAGS_32="$RPM_OPT_FLAGS"
%else
RPM_OPT_FLAGS_32=`linux32 rpm --eval %%optflags`
%endif
mkdir objs32
pushd objs32
  CFLAGS="$RPM_OPT_FLAGS_32" CC="%{__cc} -m32" \
  ../configure --shared --prefix=%{_prefix}
  %make
  make test
  ln -s ../zlib.3 .
popd
%endif

%if %{with dietlibc}
mkdir objsdietlibc
pushd objsdietlibc
  CFLAGS="-Os" CC="diet gcc" \
  ../configure --prefix=%{_prefix}
  %make libz.a
popd
%endif

%if %{with uclibc}
mkdir objsuclibc
pushd objsuclibc
  CFLAGS="%{uclibc_cflags}" CC="%{uclibc_cc}" \
  ../configure --shared --prefix=%{_prefix}
  %make
popd
%endif

%install
rm -rf %{buildroot}

install -d %{buildroot}/%{_prefix}
install -d %{buildroot}/%{_libdir}

make install -C objs prefix=%{buildroot}%{_prefix} libdir=%{buildroot}%{_libdir}
%if %{build_biarch}
make install-libs -C objs32 prefix=%{buildroot}%{_prefix}
%endif

install -d %{buildroot}/%{_lib}
mv %{buildroot}%{_libdir}/*.so.* %{buildroot}/%{_lib}/
ln -s ../../%{_lib}/libz.so.%{version} %{buildroot}%{_libdir}/

%if %{build_biarch}
install -d %{buildroot}/lib
mv %{buildroot}%{_prefix}/lib/*.so.* %{buildroot}/lib/
ln -s ../../lib/libz.so.%{version} %{buildroot}%{_prefix}/lib/
%endif

%if %{with dietlibc}
install -m644 objsdietlibc/libz.a -D %{buildroot}%{_prefix}/lib/dietlibc/lib-%{_arch}/libz.a
%endif

%if %{with uclibc}
#install -m644 objsuclibc/libz.a -D %{buildroot}%{uclibc_root}%{_libdir}/libz.a
make install-libs-only -C objsuclibc prefix=%{buildroot}%{uclibc_root} libdir=%{buildroot}%{uclibc_root}%{_libdir}
%endif

%if %mdkversion < 200900
%post -n %{lib_name} -p /sbin/ldconfig
%endif

%if %mdkversion < 200900
%postun -n %{lib_name} -p /sbin/ldconfig
%endif

%clean
rm -fr %{buildroot}

%files -n %{lib_name}
%defattr(-, root, root)
%doc README
/%{_lib}/libz.so.%{lib_major}*
%{_libdir}/libz.so.%{lib_major}*
%if %{with uclibc}
%{uclibc_root}%{_libdir}/libz.so.%{lib_major}*
%endif
%if %{build_biarch}
/lib/libz.so.*
%{_prefix}/lib/libz.so.%{lib_major}*
%endif

%files -n %{devel_name}
%defattr(-, root, root)
%doc README ChangeLog algorithm.txt
%{_mandir}/man3/zlib.3*
%{_libdir}/*.a
%{_libdir}/*.so
%if %{with uclibc}
%{uclibc_root}%{_libdir}/libz.so
%endif
%if %{build_biarch}
%{_prefix}/lib/*.a
%{_prefix}/lib/*.so
%endif
%{_includedir}/*
%if %{with dietlibc}
%{_prefix}/lib/dietlibc/lib-%{_arch}/libz.a
%endif
%if %{with uclibc}
%{uclibc_root}%{_libdir}/libz.a
%endif
