/* DO NOT EDIT.
 * Generated by ../../bin/vtkEncodeString-7.1
 * 
 * Define the vtkPointFillPassFS string.
 *
 * Generated from file: /home/nknapp/dfnworks-main/inp_2_vtk/VTK-7.1.0/Rendering/OpenGL2/glsl/vtkPointFillPassFS.glsl
 */
#include "vtkPointFillPassFS.h"
const char *vtkPointFillPassFS =
"//VTK::System::Dec\n"
"\n"
"// ============================================================================\n"
"//\n"
"//  Program:   Visualization Toolkit\n"
"//  Module:    vtkPointFillPassFS.glsl\n"
"//\n"
"//  Copyright (c) Ken Martin, Will Schroeder, Bill Lorensen\n"
"//  All rights reserved.\n"
"//  See Copyright.txt or http://www.kitware.com/Copyright.htm for details.\n"
"//\n"
"//     This software is distributed WITHOUT ANY WARRANTY; without even\n"
"//     the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR\n"
"//     PURPOSE.  See the above copyright notice for more information.\n"
"//\n"
"// ============================================================================\n"
"\n"
"// Fragment shader used by the DOF render pass.\n"
"\n"
"varying vec2 tcoordVC;\n"
"uniform sampler2D source;\n"
"uniform sampler2D depth;\n"
"uniform float nearC;\n"
"uniform float farC;\n"
"uniform float MinimumCandidateAngle;\n"
"uniform float CandidatePointRatio;\n"
"uniform vec2  pixelToTCoord;\n"
"\n"
"// the output of this shader\n"
"//VTK::Output::Dec\n"
"\n"
"void main(void)\n"
"{\n"
"  // original pixel\n"
"  float fbdepth = texture2D(depth,tcoordVC).r;\n"
"  fbdepth = 2.0*nearC/(farC + nearC -fbdepth*(farC - nearC));\n"
"  vec4  fbcolor = texture2D(source,tcoordVC);\n"
"\n"
"  vec4  closestColor = vec4(0.0,0.0,0.0,0.0);\n"
"  float closestDepth = 0.0;\n"
"  int count = 0;\n"
"\n"
"  // we track the theta range twice\n"
"  // the original values and a shifted by pi version\n"
"  // this is to deal with the cyclic nature of atan2\n"
"  // e.g. 1 degree and 359 degrees are really only 2\n"
"  // degrees apart. have to handle that.\n"
"  float minTheta = 4.0;\n"
"  float maxTheta = -4.0;\n"
"  float minTheta2 = 4.0;\n"
"  float maxTheta2 = -4.0;\n"
"\n"
"  // loop over pixels\n"
"  for (int i = -3; i <= 3; i++)\n"
"    {\n"
"    for (int j = -3; j <= 3; j++)\n"
"      {\n"
"      float adepth = texture2D(depth,tcoordVC + pixelToTCoord*vec2(i,j)).r;\n"
"      float mdepth = 2.0*nearC/(farC + nearC -adepth*(farC - nearC));\n"
"      if (mdepth < fbdepth*CandidatePointRatio && (i != 0 || j != 0))\n"
"        {\n"
"        float theta = atan(float(j),float(i));\n"
"        minTheta = min(minTheta,theta);\n"
"        maxTheta = max(maxTheta,theta);\n"
"        if (theta > 0)\n"
"          {\n"
"          theta -= 3.1415926;\n"
"          }\n"
"        else\n"
"          {\n"
"          theta += 3.1415926;\n"
"          }\n"
"        minTheta2 = min(minTheta2,theta);\n"
"        maxTheta2 = max(maxTheta2,theta);\n"
"        count = count + 1;\n"
"        closestColor += texture2D(source,tcoordVC + pixelToTCoord*vec2(i,j));\n"
"        closestDepth += adepth;\n"
"        }\n"
"      }\n"
"    }\n"
"\n"
"// must be at least the candidate angle of support\n"
"if (min(maxTheta-minTheta, maxTheta2-minTheta2) > MinimumCandidateAngle)\n"
"  {\n"
"  gl_FragData[0] = closestColor/count;\n"
"  gl_FragDepth = closestDepth/count;\n"
"  }\n"
"else\n"
"  {\n"
"  gl_FragData[0] = fbcolor;\n"
"  gl_FragDepth = fbdepth;\n"
"  }\n"
"}\n"
"\n";

